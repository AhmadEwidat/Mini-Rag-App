from fastapi import FastAPI,APIRouter
import os
base_router=APIRouter(
    prefix="/api/v1",
    tags=["api_v1"]
)
app_name=os.getenv("APP_NAME")
app_version=os.getenv("APP_VERSION")
@base_router.get("/")
async def welcome():
    return {"app_name":app_name,"app_version":app_version,"message":"Welcome to the Mini-Rag-App API"}