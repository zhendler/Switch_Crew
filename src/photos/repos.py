from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.models import Photo, Tag


class PhotoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tag(self, url_link: str, description: str, qr_core_url: str, owner_id: int, tags: list[str]):
        new_photo = Photo(
            url_link=url_link,
            description=description,
            qr_core_url=qr_core_url,
            owner_id=owner_id,
        )
        self.db.add(new_photo)
        await self.db.commit()
        await self.db.refresh(new_photo)

        for tag_name in tags:
            tag = await self.db.scalar(select(Tag).where(Tag.name == tag_name))
            if not tag:
                tag = Tag(name=tag_name)
                self.db.add(tag)
            new_photo.tags.append(tag)

        await self.db.commit()
        await self.db.refresh(new_photo)
        return new_photo

    async def get_all_photos(self):
        photos = await self.db.execute(select(Photo))
        return photos.scalars().all()