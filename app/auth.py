"""
User-session authentication.

Design: on login we create a random opaque token, store it server-side in
the `sessions` table with an expiry, and hand the client an HttpOnly
cookie containing that token. `require_session` (a FastAPI dependency)
looks the token up on every write request and rejects anything missing,
unknown, or expired. This is deliberately server-verified session state,
not a self-contained/stateless token (e.g. a bare JWT) — logout actually
invalidates the session because the row is deleted.
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException, Response, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session as DBSession

from app.database import get_db
from app.models import Session as SessionModel
from app.models import User

SESSION_COOKIE_NAME = "bookstore_session"
SESSION_MAX_AGE = int(os.environ.get("SESSION_MAX_AGE", "86400"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_session(db: DBSession, user: User, response: Response) -> SessionModel:
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_MAX_AGE)
    session = SessionModel(user_id=user.id, expires_at=expires_at)
    db.add(session)
    db.commit()
    db.refresh(session)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        # `secure=True` is intentionally left off so the API is testable
        # over plain HTTP via the Swagger UI / docker-compose locally.
        # Set it to True behind HTTPS in production.
    )
    return session


def destroy_session(db: DBSession, token: str | None, response: Response) -> None:
    if token:
        db.query(SessionModel).filter(SessionModel.token == token).delete()
        db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME)


def require_session(
    bookstore_session: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
) -> User:
    """Dependency for write endpoints. Raises 401 unless a valid,
    unexpired session cookie is present."""
    if not bookstore_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session = (
        db.query(SessionModel)
        .filter(SessionModel.token == bookstore_session)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
