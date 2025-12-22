from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.core.settings.settings import settings
from app.models.auth_identity import AuthIdentity

router = APIRouter(prefix="/auth/supabase", tags=["supabase"])


@router.post("/webhook")
async def supabase_webhook(
    payload: dict,
    x_service_role: str | None = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
):
    """Receive Supabase Auth webhook and sync email confirmation to main DB.

    Minimal verification: require header `X-Service-Role` to match configured service role key.
    Payload is expected to include a `user` object with `email` and `email_confirmed_at`.
    """
    if not x_service_role or x_service_role != settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    user = payload.get("user") or payload.get("record") or {}
    email = user.get("email") if isinstance(user, dict) else None
    confirmed = bool(user.get("email_confirmed_at")) if isinstance(user, dict) else False

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing user email in payload")

    if confirmed:
        stmt = (
            update(AuthIdentity)
            .where(AuthIdentity.email == email)
            .values(is_verified=True)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(stmt)
        await db.commit()

    return {"status": "ok"}
