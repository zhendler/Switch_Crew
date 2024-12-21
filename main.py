from fastapi import FastAPI
from config.db import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from src.tags.repos import TagRepository

app = FastAPI()

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

@app.post("/tags/")
async def create_tag(name: str, db: Session = Depends(get_db)):
    tag_repo = TagRepository(db)
    tag = await tag_repo.create_tag(name=name)
    return tag

@app.get('/tags/all')
async def get_all_tags(db: Session = Depends(get_db)):
    tag_repo = TagRepository(db)
    return await tag_repo.get_all_tags()

@app.get('/tags/{tag_name}')
async def get_tag_by_name(tag_name: str, db: Session = Depends(get_db)):
    tag_repo = TagRepository(db)
    tag = await tag_repo.get_tag_by_name(tag_name)
    return tag

@app.delete('/tags/delete/{tag_name}')
async def delete_tag_by_name(tag_name: str, db: Session = Depends(get_db)):
    tag_repo = TagRepository(db)
    tag = await tag_repo.delete_tag_by_name(tag_name)
    return tag

@app.put('/tags/update/{tag_name}-{tag_new_name}')
async def update_tag_name(tag_name: str, tag_new_name: str, db: Session = Depends(get_db)):
    tag_repo = TagRepository(db)
    tag = await tag_repo.update_tag_name(tag_name, tag_new_name)
    return tag