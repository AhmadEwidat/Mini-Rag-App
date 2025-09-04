from fastapi import FastAPI,APIRouter,Depends,UploadFile,status
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings,Settings
from controllers import DataController,ProjectController,ProcessController
from models import ResponseSiginal
import aiofiles
import logging
from.schemes.data import proccessRequest

logger=logging.getLogger("uvicorn.error")
dataController=DataController()
data_router=APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1","data"]
)
@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file:UploadFile, app_settings:Settings = Depends(get_settings)):

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
    return JSONResponse(content={"message":ResponseSiginal.FILE_UPLOADED_SUCCESS.value
                                 ,"file_id":file_id})

@data_router.post("/process/{project_id}")
async def process_data(project_id: str, process_request: proccessRequest):
   file_id=process_request.file_id
   chunk_size=process_request.chunk_size
   overlap=process_request.overlap
   processController=ProcessController(project_id=project_id)
   file_contents=processController.get_file_content(file_id=file_id)
   chunks=processController.process_file_content(file_contents=file_contents,
                                                 file_id=file_id,
                                                 chunk_size=chunk_size,
                                                    overlap=overlap)
   if chunks is None or len(chunks)==0:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,content={"signal":ResponseSiginal.PROCESSING_FAILED.value})
   return chunks