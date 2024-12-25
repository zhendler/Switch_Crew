from sqlalchemy.orm import Session
from photos.models import Photo
from photos.schemas import PhotoCreate


def create_photo(db: Session, photo: PhotoCreate, user_id: int):
    db_photo = Photo(**photo.dict(), user_id=user_id)
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo


def update_photo_description(db: Session, photo_id: int, new_description: str):
    db_photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    db_photo.description = new_description
    db.commit()
    db.refresh(db_photo)
    return db_photo


def delete_photo(db: Session, photo_id: int):
    db_photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    db.delete(db_photo)
    db.commit()
    return {"message": "Photo deleted successfully"}