from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db
from src.models.models import Report
from src.reports.repos import ReportRepository
from src.reports.schemas import ReportCommentCreate, ReportPhotoCreate

report_router = APIRouter()



@report_router.post("/report_comment")
async def report_comment(request: Request,
                         report: ReportCommentCreate,
                         db: AsyncSession = Depends(get_db)
                         ):
    if not report.comment_id:
        raise HTTPException(status_code=400, detail="Comment id is required")


    report_repo = ReportRepository(db)
    result = await report_repo.create_report(report)
    return result

@report_router.post("/report_photo")
async def report_photo(request: Request,
                         report: ReportPhotoCreate,
                         db: AsyncSession = Depends(get_db)
                         ):
    if not report.cphoto_id:
        raise HTTPException(status_code=400, detail="Photo id is required")


    report_repo = ReportRepository(db)
    result = await report_repo.create_report(report)
    return result

