from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from core.database import get_session
from schemas.reports import RecognitionResultPublic, RecognitionResult

reports_router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


@reports_router.get("/", response_model=list[RecognitionResultPublic])
async def read_results(
        *,
        session: Session = Depends(get_session),
        offset: int = 0,
        limit: int = Query(default=10, le=10),
):
    results = session.exec(select(RecognitionResult).offset(offset).limit(limit)).all()
    return results