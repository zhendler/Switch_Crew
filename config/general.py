from pydantic_settings import BaseSettings
import cloudinary
from dotenv import load_dotenv
import os

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)



class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()