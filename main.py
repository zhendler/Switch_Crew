from fastapi import FastAPI
from src.tags.routers import tag_router

app = FastAPI()

app.include_router(tag_router, prefix='/tags', tags=['tags'])

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

