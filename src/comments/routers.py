from fastapi import APIRouter, Query, Path, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db

router = APIRouter()


@router.get("/{photo_id}/comments")
async def create_comment() :
    pass