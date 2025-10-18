from .BaseController import BaseController
from models.db_schemes import Project, DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json
import logging

class NLPController(BaseController):

    def __init__(self, vectordb_client, generation_client, 
                 embedding_client, template_parser):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        self.logger = logging.getLogger(__name__)

    def create_collection_name(self, project_id: str):
        return f"collection_{project_id}".strip()
    
    def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)
    
    def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)

        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )
    
    def index_into_vector_db(self, project: Project, chunks: List[DataChunk],
                                   chunks_ids: List[int], 
                                   do_reset: bool = False):
        
        # step1: get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step2: manage items
        texts = [ c.chunk_text for c in chunks ]
        metadata = [ c.chunk_metadata for c in  chunks]
        vectors = [
            self.embedding_client.embed_text(text=text, 
                                             document_type=DocumentTypeEnum.DOCUMENT.value)
            for text in texts
        ]

        # step3: create collection if not exists
        _ = self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )

        # step4: insert into vector db
        _ = self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            record_ids=chunks_ids,
        )

        return True

    def search_vector_db_collection(self, project: Project, text: str, limit: int = 10):

        try:
            # step1: get collection name
            collection_name = self.create_collection_name(project_id=project.project_id)
            self.logger.info(f"Searching collection: {collection_name}")

            # step2: get text embedding vector
            self.logger.info(f"Generating embedding for query: {text}")
            vector = self.embedding_client.embed_text(text=text, 
                                                     document_type=DocumentTypeEnum.QUERY.value)

            if not vector or len(vector) == 0:
                self.logger.error("Failed to generate embedding vector")
                return False

            self.logger.info(f"Generated embedding vector with {len(vector)} dimensions")

            # step3: do semantic search
            self.logger.info(f"Performing vector search with limit: {limit}")
            results = self.vectordb_client.search_by_vector(
                collection_name=collection_name,
                vector=vector,
                limit=limit
            )

            if not results:
                self.logger.warning("Vector search returned no results")
                return False

            self.logger.info(f"Vector search returned {len(results)} results")
            return results

        except Exception as exc:
            self.logger.exception(f"Error in search_vector_db_collection: {exc}")
            return False
    
    def answer_rag_question(self, project: Project, query: str, limit: int = 10):
        
        answer, full_prompt, chat_history = None, None, None

        try:
            # step1: retrieve related documents
            self.logger.info(f"Starting RAG process for project {project.project_id} with query: {query}")
            retrieved_documents = self.search_vector_db_collection(
                project=project,
                text=query,
                limit=limit,
            )

            if not retrieved_documents or len(retrieved_documents) == 0:
                self.logger.warning(f"No documents retrieved for query: {query}")
                return answer, full_prompt, chat_history
            
            self.logger.info(f"Retrieved {len(retrieved_documents)} documents for query")
            
            # step2: Construct LLM prompt
            system_prompt = self.template_parser.get("rag", "system_prompt")
            if not system_prompt:
                self.logger.error("Failed to get system prompt from template parser")
                return answer, full_prompt, chat_history

            documents_prompts = "\n".join([
                self.template_parser.get("rag", "document_prompt", {
                        "doc_num": idx + 1,
                        "chunk_text": doc.text,
                })
                for idx, doc in enumerate(retrieved_documents)
            ])

            footer_prompt = self.template_parser.get("rag", "footer_prompt")
            if not footer_prompt:
                self.logger.error("Failed to get footer prompt from template parser")
                return answer, full_prompt, chat_history

            # step3: Construct Generation Client Prompts
            chat_history = [
                self.generation_client.construct_prompt(
                    prompt=system_prompt,
                    role=self.generation_client.enums.SYSTEM.value,
                )
            ]

            full_prompt = "\n\n".join([ documents_prompts,  footer_prompt])
            self.logger.info(f"Constructed full prompt with {len(full_prompt)} characters")

            # step4: Retrieve the Answer
            self.logger.info("Calling generation client to generate answer")
            answer = self.generation_client.generate_text(
                prompt=full_prompt,
                chat_history=chat_history
            )

            if not answer:
                self.logger.error("Generation client returned None answer")
            else:
                self.logger.info(f"Successfully generated answer with {len(answer)} characters")

        except Exception as exc:
            self.logger.exception(f"Error in answer_rag_question: {exc}")

        return answer, full_prompt, chat_history