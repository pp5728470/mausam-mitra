from datetime import datetime, timezone
from uuid import UUID
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.enums import AlertStatus, RecipientScope, Role
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertListResponse, AlertResponse

router = APIRouter(tags=["alerts"])



def get_alert_filter(current_user: User):
    if current_user.role == Role.CITIZEN:
        # Citizens only see their direct alerts
        return Alert.recipient_user_id == current_user.id
    else:
        # Each event generates a specific alert copy for each operational scope (ADMIN, ANALYST, VERIFIER).
        # Therefore, querying only for the user's exact role scope prevents duplicates.
        scopes = []
        if current_user.role == Role.ADMIN:
            scopes = [RecipientScope.ADMIN]
        elif current_user.role == Role.ANALYST:
            scopes = [RecipientScope.ANALYST]
        elif current_user.role == Role.VERIFIER:
            scopes = [RecipientScope.VERIFIER]

        return Alert.recipient_scope.in_(scopes) | (Alert.recipient_user_id == current_user.id)


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: AlertStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List alerts relevant to the current user.
    """
    filter_cond = get_alert_filter(current_user)

    query = select(Alert).where(filter_cond)
    count_query = select(func.count()).select_from(Alert).where(filter_cond)
    unread_query = select(func.count()).select_from(Alert).where(filter_cond).where(Alert.status == AlertStatus.UNREAD)

    if status_filter:
        query = query.where(Alert.status == status_filter)
        count_query = count_query.where(Alert.status == status_filter)

    query = query.order_by(Alert.created_at.desc()).limit(limit).offset(offset)

    total = await db.scalar(count_query)
    unread_count = await db.scalar(unread_query)
    items = (await db.scalars(query)).all()

    return AlertListResponse(items=items, total=total or 0, unread_count=unread_count or 0)


@router.get("/unread-count", response_model=Dict[str, int])
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the number of unread alerts for the current user."""
    filter_cond = get_alert_filter(current_user)
    unread_query = select(func.count()).select_from(Alert).where(filter_cond).where(Alert.status == AlertStatus.UNREAD)
    unread_count = await db.scalar(unread_query)
    
    return {"unread_count": unread_count or 0}


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific alert by ID."""
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        
    # Check if the alert matches the user's filter
    filter_cond = get_alert_filter(current_user)
    stmt = select(func.count()).select_from(Alert).where(Alert.id == alert_id).where(filter_cond)
    has_access = await db.scalar(stmt)
    
    if not has_access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        
    return alert


@router.patch("/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_read(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a specific alert as READ."""
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    filter_cond = get_alert_filter(current_user)
    stmt = select(func.count()).select_from(Alert).where(Alert.id == alert_id).where(filter_cond)
    has_access = await db.scalar(stmt)
    
    if not has_access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if alert.status == AlertStatus.UNREAD:
        alert.status = AlertStatus.READ
        alert.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(alert)
    return alert


@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
async def mark_alert_acknowledged(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a specific alert as ACKNOWLEDGED."""
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    filter_cond = get_alert_filter(current_user)
    stmt = select(func.count()).select_from(Alert).where(Alert.id == alert_id).where(filter_cond)
    has_access = await db.scalar(stmt)
    
    if not has_access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if alert.status in (AlertStatus.UNREAD, AlertStatus.READ):
        alert.status = AlertStatus.ACKNOWLEDGED
        now = datetime.now(timezone.utc)
        alert.acknowledged_at = now
        if not alert.read_at:
            alert.read_at = now
        await db.commit()
        await db.refresh(alert)
    return alert

