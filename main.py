from fastapi import FastAPI
from src.photos.routers import photo_router

# from src.tags.routers import tag_router


app = FastAPI()


# app.include_router(tag_router, prefix='/tags', tags=['tags'])
app.include_router(photo_router, prefix="/photos", tags=["photos"])


@app.get("/ping")
async def ping():
    return {"ping": "pong"}
