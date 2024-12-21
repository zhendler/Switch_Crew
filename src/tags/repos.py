from http.client import HTTPException

from sqlalchemy.orm import Session
from .models import Tag
from sqlalchemy.future import select

class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_tag_by_name(self, tag_name: str):
        tag = select(Tag).filter(Tag.name == tag_name)
        result = await self.db.execute(tag)
        return result.scalars().first()

    async def create_tag(self, tag_name: str):
        new_tag = Tag(name=tag_name)
        self.db.add(new_tag)
        await self.db.commit()
        await self.db.refresh(new_tag)
        return new_tag

    async def get_all_tags(self):
        tags = await self.db.execute(select(Tag))
        return tags.scalars().all()

    async def delete_tag_by_name(self, tag_name: str):
        tag = select(Tag).filter(Tag.name == tag_name)
        result = await self.db.execute(tag)
        tag = result.scalars().first()
        if tag:
            await self.db.delete(tag)
            await self.db.commit()
            return "Successfully deleted!"
        else:
            return "Tag not found!"

    async def update_tag_name(self, tag_name: str, tag_new_name: str):
        tag = select(Tag).filter(Tag.name == tag_name)
        result = await self.db.execute(tag)
        tag = result.scalars().first()

        if tag:
            tag.name = tag_new_name
            await self.db.commit()
            await self.db.refresh(tag)
            return tag
        else:
            return HTTPException(status_code=404, detail="Tag not found!")

