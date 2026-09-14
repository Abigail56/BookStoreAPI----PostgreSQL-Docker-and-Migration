from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Author ----------


class AuthorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    bio: str | None = None


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    bio: str | None = None


class AuthorOut(AuthorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AuthorWithBooks(AuthorOut):
    books: list["BookOut"] = []


# ---------- Book ----------


class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    isbn: str | None = Field(None, max_length=20)
    published_year: int | None = Field(None, ge=0, le=2100)
    author_id: int


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    isbn: str | None = Field(None, max_length=20)
    published_year: int | None = Field(None, ge=0, le=2100)
    author_id: int | None = None


class BookOut(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


AuthorWithBooks.model_rebuild()


# ---------- Auth ----------


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str
