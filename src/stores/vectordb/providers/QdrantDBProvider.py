from qdrant_client import models, QdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
import logging
from typing import List
from models.db_schemes import RetrievedDocument

class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_path: str, distance_method: str):

        self.client = None
        self.db_path = db_path
        self.distance_method = None

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.client = QdrantClient(path=self.db_path)

    def disconnect(self):
        self.client = None

    def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)
    
    def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    
    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name):
            return self.client.delete_collection(collection_name=collection_name)
        
    def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        if do_reset:
            _ = self.delete_collection(collection_name=collection_name)
        
        # If collection exists, verify its vector size matches the requested embedding size.
        if self.is_collection_existed(collection_name):
            try:
                info = self.client.get_collection(collection_name=collection_name)
                # Qdrant local client returns a models.CollectionInfo with nested config
                # Different client versions expose size via: info.config.params.vectors.size
                # Fallbacks are used to avoid attribute errors across versions.
                configured_size = None
                if hasattr(info, "config") and hasattr(info.config, "params") and hasattr(info.config.params, "vectors"):
                    vectors_cfg = info.config.params.vectors
                    # vectors could be a dict or VectorParams
                    if hasattr(vectors_cfg, "size"):
                        configured_size = vectors_cfg.size
                    elif isinstance(vectors_cfg, dict) and "size" in vectors_cfg:
                        configured_size = vectors_cfg.get("size")

                if configured_size is not None and int(configured_size) != int(embedding_size):
                    # Recreate with the correct size
                    _ = self.client.delete_collection(collection_name=collection_name)
                else:
                    # Already exists with correct size; nothing to do
                    return False
            except Exception as e:
                # If we fail to read config, try to recreate to be safe
                self.logger.warning(f"Failed to read collection config for {collection_name}: {e}. Recreating with size {embedding_size}.")
                _ = self.client.delete_collection(collection_name=collection_name)
        
        # Create collection (either fresh or after deletion)
        _ = self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=embedding_size,
                distance=self.distance_method
            )
        )

        return True
        
        return False
    
    def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        
        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False
        
        try:
            _ = self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        id=[record_id],
                        vector=vector,
                        payload={
                            "text": text, "metadata": metadata
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

        return True
    
    def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = list(range(0, len(texts)))

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.Record(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x], "metadata": batch_metadata[x]
                    }
                )

                for x in range(len(batch_texts))
            ]

            try:
                _ = self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records,
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True
        
    def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
        # Guard against empty or mismatched-dimension collections causing local cosine calc errors
        try:
            info = self.client.get_collection(collection_name=collection_name)
        except Exception:
            info = None

        # Try to extract points_count and configured size in a version-tolerant way
        points_count = None
        configured_size = None
        try:
            if info is not None:
                if hasattr(info, "points_count"):
                    points_count = info.points_count
                if hasattr(info, "config") and hasattr(info.config, "params") and hasattr(info.config.params, "vectors"):
                    vectors_cfg = info.config.params.vectors
                    if hasattr(vectors_cfg, "size"):
                        configured_size = vectors_cfg.size
                    elif isinstance(vectors_cfg, dict) and "size" in vectors_cfg:
                        configured_size = vectors_cfg.get("size")
        except Exception:
            pass

        # If collection is empty, avoid calling search which may error in local backend
        if points_count is not None and int(points_count) == 0:
            # If size mismatches and collection is empty, recreate with the correct size inferred from query vector
            if configured_size is not None and int(configured_size) != int(len(vector)):
                try:
                    _ = self.client.delete_collection(collection_name=collection_name)
                    _ = self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=len(vector),
                            distance=self.distance_method
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to recreate empty collection {collection_name} with size {len(vector)}: {e}")
            return None

        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Error during vector search in collection {collection_name}: {e}")
            return None

        if not results or len(results) == 0:
            return None
        
        return [
            RetrievedDocument(**{
                "score": result.score,
                "text": result.payload["text"],
            })
            for result in results
        ]