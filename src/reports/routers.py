from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db
from src.auth.utils import get_current_user
from src.models.models import Report, User
from src.reports.repos import ReportRepository
from src.reports.schemas import ReportCommentCreate, ReportPhotoCreate, ReportPhotoResponse, ReportStatus

report_router = APIRouter()



# @report_router.post("/report_comment")
# async def report_comment(request: Request,
#                          report: ReportCommentCreate,
#                          db: AsyncSession = Depends(get_db)
#                          ):
#     if not report.comment_id:
#         raise HTTPException(status_code=400, detail="Comment id is required")
#
#
#     report_repo = ReportRepository(db)
#     result = await report_repo.create_report(report)
#     return result

@report_router.get("/user_reports",
                   response_model=list[ReportPhotoResponse],
                   status_code=200)
async def get_user_reports(user_id: int,
                           db: AsyncSession = Depends(get_db)):
    report_repo = ReportRepository(db)
    return await report_repo.get_user_reports(user_id)


@report_router.post("/report_photo",
                    response_model=ReportPhotoResponse,
                    status_code=201)
async def report_photo(
    report: ReportPhotoCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report_repo = ReportRepository(db)

    # Перевіряємо, чи існує фото перед створенням скарги
    photo_exists = await report_repo.check_photo_exists(report.photo_id)
    if not photo_exists:
        raise HTTPException(status_code=404, detail="Photo not found")

    result = await report_repo.create_photo_report(report, user.id, photo_exists)
    return result


@report_router.post("/resolve_report")
async def resolve_report(report_id: int,
                         status: ReportStatus,
                         db: AsyncSession = Depends(get_db)):
    report_repo = ReportRepository(db)
    return await report_repo.resolve_report(report_id, status)
