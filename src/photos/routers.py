from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from photos.schemas import PhotoCreate, PhotoResponse, PhotoUpdate
from config.db import get_db
from photos.models import Photo
from typing import List
from photos.repos import create_photo, update_photo_description, delete_photo

photo_router = APIRouter()

@photos_router.post("/", response_model=PhotoResponse)
def upload_photo(photo: PhotoCreate, db: Session = Depends(get_db), user_id: int = 1):
    db_photo = create_photo(db, photo, user_id)
    return db_photo

@photos_router.get("/{photo_id}", response_model=PhotoResponse)
def get_photo_by_id(photo_id: int, db: Session = Depends(get_db)):
    db_photo = get_photo(db, photo_id)
    if db_photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return db_photo

@photos_router.put("/{photo_id}", response_model=PhotoResponse)
def update_photo(photo_id: int, photo: PhotoUpdate, db: Session = Depends(get_db)):
    update_photo = update_photo_description(db, photo_id, photo_data.description)
    return update_photo

@photos_router.delete("/{photo_id}")
def delete_photo_by_id(photo_id: int, db: Session = Depends(get_db)):
    delete_photo(db, photo_id)
    return {"message": "Photo deleted successfully"}