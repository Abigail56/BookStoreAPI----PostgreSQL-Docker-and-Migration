"""
ORM models.

Author (1) --- (many) Book, via Book.author_id -> Author.id.

User / Session back the session-based authentication used to protect
write endpoints (POST / PUT / DELETE) on /authors and /books.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Author(SQLModel, table=True):
    __tablename__ = "authors"

    id: int | None = Field(default=None, primary_key=True, index=True)
    name: str = Field(max_length=200, index=True)
    bio: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)

    books: list[Book] = Relationship(
        back_populates="author",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )


class Book(SQLModel, table=True):
    __tablename__ = "books"

    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(max_length=300, index=True)
    isbn: str | None = Field(default=None, max_length=20, unique=True)
    published_year: int | None = Field(default=None)
    author_id: int = Field(
        foreign_key="authors.id",
        ondelete="CASCADE",
        index=True,
    )
    created_at: datetime = Field(default_factory=_utcnow)

    author: Author = Relationship(back_populates="books")


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True, index=True)
    username: str = Field(max_length=100, unique=True, index=True)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=_utcnow)


class Session(SQLModel, table=True):
    """A server-side session record. The opaque token is what's stored
    in the client's session cookie; the DB row is the source of truth
    for whether that session is still valid, so logout / expiry are
    enforced server-side rather than trusting the cookie alone."""

    __tablename__ = "sessions"

    id: int | None = Field(default=None, primary_key=True, index=True)
    token: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        max_length=64,
        unique=True,
        index=True,
    )
    user_id: int = Field(
        foreign_key="users.id",
        ondelete="CASCADE",
        index=True,
    )
    created_at: datetime = Field(default_factory=_utcnow)
    expires_at: datetime
