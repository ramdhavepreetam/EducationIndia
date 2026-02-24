from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.dependencies import verify_token
from app.modules.analysis.service import analysis_service
from app.modules.analysis.schemas import ReportSchema

router = APIRouter()

@router.get("/attempts/{attempt_id}/report", response_model=ReportSchema)
async def get_report(
    attempt_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """
    Get the full analysis report for a submitted attempt.
    Authorized for the student who owns it, their linked parent, or an admin.
    """
    user_id = UUID(user["sub"])
    role = user.get("user_role", "student")
    
    return await analysis_service.get_attempt_report(attempt_id, user_id, role, db)
