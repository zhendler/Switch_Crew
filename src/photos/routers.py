from fastapi import Depends, APIRouter
photo_router = APIRouter()
from .repos import PhotoRepository
from sqlalchemy.ext.asyncio import AsyncSession
from config.db import get_db
from fastapi import Query, Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@photo_router.post("/create/")
async def create_tag(
    url_link: str = Query(..., description="photo's URL"),
    description: str = Query(..., description="photo description"),
    qr_core_url: str = Query(..., description="URL for QR"),
    owner_id: int = Query(..., description="owner's ID "),
    tags: list[str] = Query(..., description="list of tags"),
    db: AsyncSession = Depends(get_db),
):
    photo_repo = PhotoRepository(db)
    photo = await photo_repo.create_tag(
        url_link=url_link,
        description=description,
        qr_core_url=qr_core_url,
        owner_id=owner_id,
        tags=tags,
    )
    return photo

@photo_router.get('/')
async def get_all_photos(request: Request, db: AsyncSession = Depends(get_db)):
    photo_repo = PhotoRepository(db)
    photos =await photo_repo.get_all_photos()
    return templates.TemplateResponse("photos_by_tag.html",
            {"request": request, "title": 'All Photos', "photos": photos})
