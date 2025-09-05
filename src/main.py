from fastapi import FastAPI
from routes.base import base_router
from routes.data import data_router
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
app=FastAPI()
@app.on_event("startup")
async def startup_db_client():
    settings=get_settings()
    app.mongodb_connection=AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client=app.mongodb_connection[settings.MONGODB_DB_NAME]
    
@ app.on_event("shutdown")
async def shutdown_db_client(): 
    app.mongodb_connection.close()

app.include_router(base_router)
app.include_router(data_router)
