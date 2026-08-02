"""Screen Time Ingestion API Endpoints. Owner: Backend & Integrations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.di import get_budgeted_llm_provider, get_current_user_id, get_db
from app.providers.llm.base import LLMProvider, LLMProviderUnavailable
from app.providers.llm.budget import LLMBudgetExceeded
from app.services.rate_limiter import check_rate_limit
from app.services.screentime.service import (
    ScreenTimeAnalysisResult,
    process_screentime_payload,
)
from app.services.screentime.vision import extract_apps_from_screenshot, guess_mime_type

router = APIRouter(prefix="/screentime", tags=["screentime"])


class ScreenTimeUploadBody(BaseModel):
    apps: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Parsed or manual list of app usages: [{appName: 'Instagram', durationMinutes: 120}]",
    )


@router.post("/analyze", response_model=ScreenTimeAnalysisResult)
def analyze_screentime_json(
    body: ScreenTimeUploadBody,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> ScreenTimeAnalysisResult:
    """Analyze structured screen time JSON and ingest evidence events into the database."""
    check_rate_limit("screentime", user_id, limit=10, window_seconds=60)

    if not body.apps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one app with durationMinutes, or upload a screenshot.",
        )

    return process_screentime_payload(db, user_id, body.apps, ocr_source="manual")


@router.post("/upload", response_model=ScreenTimeAnalysisResult)
async def upload_screentime_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    llm: LLMProvider = Depends(get_budgeted_llm_provider),
) -> ScreenTimeAnalysisResult:
    """Accept iOS/Android Screen Time screenshot, OCR via vision LLM, classify, schedule."""
    check_rate_limit("screentime_upload", user_id, limit=10, window_seconds=60)

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(contents) > 12 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Screenshot too large (max 12MB).",
        )

    filename = file.filename or "screentime.png"
    mime = guess_mime_type(filename, file.content_type)

    try:
        parsed_apps = extract_apps_from_screenshot(llm, contents, mime_type=mime)
    except LLMBudgetExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except LLMProviderUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vision OCR temporarily unavailable: {exc}",
        ) from exc
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Configured LLM provider cannot OCR images. Set LLM_PROVIDER=gemini.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to OCR screenshot: {exc}",
        ) from exc

    return process_screentime_payload(db, user_id, parsed_apps, ocr_source="vision")
