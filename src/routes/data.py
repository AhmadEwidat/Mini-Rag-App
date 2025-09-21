from fastapi import FastAPI,APIRouter,Depends,UploadFile,status,Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings,Settings
from controllers import DataController,ProjectController,ProcessController
from models import ResponseSiginal
import aiofiles
import logging
from.schemes.data import ProccessRequest
from models.ProjectModel import ProjectModel
from models.db_schemes import DataChunk,Asset
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.enums.AssetTypeEnum import AssetTypeEnum

logger=logging.getLogger("uvicorn.error")
dataController=DataController()
data_router=APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1","data"]
)
@data_router.post("/upload/{project_id}")
async def upload_data(request:Request,project_id: str, file:UploadFile, app_settings:Settings = Depends(get_settings)):
    project_model=await ProjectModel.create_instance(db_client=request.app.db_client)
    project=  await project_model.get_project_or_create_one(project_id=project_id)

    is_valid,result_signal =dataController.validate_file (file)
    if not is_valid:
    #     return JSONResponse(status_code=status.HTTP_200_OK,content={"message":result_signal})
    # else:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"message":result_signal})  
    
    project_dir_path=ProjectController().get_project_path(project_id=project_id)
    file_path,file_id=dataController.genarate_unique_filepath(original_filename=file.filename,project_id=project_id)
    try:
        async with aiofiles.open(file_path,'wb') as out_file:
         while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
            await out_file.write(chunk)
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"message":ResponseSiginal.FILE_UPLOADED_FAILED.value,"error":str(e)})
    asset_model= await AssetModel.create_instance(db_client=request.app.db_client)
    asser_resourse=Asset(
        asset_name=file_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_size=os.path.getsize(file_path),
        asset_path=file_path,
        asset_project_id=project.id
    )
    asset_record=await asset_model.create_asset(asser_resourse)
    return JSONResponse(content={"message":ResponseSiginal.FILE_UPLOADED_SUCCESS.value
                                 ,"file_id":str(asset_record.id)})

@data_router.post("/process/{project_id}")
async def process_data(request:Request,project_id: str, process_request: ProccessRequest):
   
   chunk_size=process_request.chunk_size
   overlap=process_request.overlap
   do_reset=process_request.do_reset

   project_model= await ProjectModel.create_instance(db_client=request.app.db_client)
   project=  await project_model.get_project_or_create_one(project_id=project_id)
   
   project_file_ids={}
   asset_model= await AssetModel.create_instance(db_client=request.app.db_client)
   if process_request.file_id:
    asset_record= await asset_model.get_asset_record(project_id=project.id,asset_name=process_request.file_id)
    if asset_record is None:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSiginal.NO_FILES_TO_PROCESS.value})
    project_file_ids={
        asset_record.id:asset_record.asset_name
    }
   else:
   
    project_files= await asset_model.get_all_project_assets(asseet_project_id=project.id,asset_type=AssetTypeEnum.FILE.value)
    project_file_ids={record.id:record.asset_name for record in project_files}

   if len(project_file_ids)==0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSiginal.NO_FILES_TO_PROCESS.value})
   
   processController=ProcessController(project_id=project_id)
   no_records=0
   no_files=0
   chunk_model=await ChunkModel.create_instance(db_client=request.app.db_client) 

   if do_reset==1:
        _=await chunk_model.delete_chunks_by_ids(project_id=project.id)
   for asset_id,file_id in project_file_ids.items():
   
        file_contents=processController.get_file_content(file_id=file_id)
        if file_contents is None:
           logger.error(f"Error processing file: {file_id}")
           continue
           
        chunks=processController.process_file_content(file_contents=file_contents,
                                                        file_id=file_id,
                                                        chunk_size=chunk_size,
                                                            overlap=overlap)
        if chunks is None or len(chunks)==0:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSiginal.PROCESSING_FAILED.value})
        

        file_chunks_records=[
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_meta=chunk.metadata,
                chunk_order=i+1,
                chunk_project_id=project.id,
                chunk_asset_id=asset_id
                
                    )
            for i,chunk in enumerate(chunks)
        ]
        
        
        no_records+=await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files+=1

   return JSONResponse(content ={"signal":ResponseSiginal.PROCESSING_SUCCESS.value
                                            ,"no_of_chunks":no_records
                                            ,"no_of_files":no_files
                                        })