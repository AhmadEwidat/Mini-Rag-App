from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    App_Name: str 
    App_Version: str
    File_Allowed_Types: list
    Max_File_Size: int
    FILE_DEFAULT_CHUNK_SIZE: int
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    class Config:
        env_file = ".env"


def get_settings():
    settings = Settings()
    return settings