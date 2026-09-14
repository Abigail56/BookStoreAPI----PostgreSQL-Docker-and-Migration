from fastapi import Cookie, Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.auth import (
    create_session,
    destroy_session,
    hash_password,
    require_session,
    verify_password,
)
from app.database import get_db
from app.models import User

app = FastAPI(
    title="Bookstore API",
    description=(
        "CRUD API for authors and books, backed by PostgreSQL and "
        "Alembic migrations. Write endpoints (POST/PUT/DELETE) require "
        "a logged-in session — call /auth/register then /auth/login "
        "from this Swagger UI first (it will keep the session cookie "
        "for subsequent requests)."
    ),
    version="1.0.0",
)


# ============================================================
# Auth
# ============================================================


@app.post("/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    user = User(username=user_in.username, hashed_password=hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.UserOut, tags=["auth"])
def login(credentials: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    create_session(db, user, response)
    return user


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["auth"])
def logout(
    response: Response,
    db: Session = Depends(get_db),
    bookstore_session: str | None = Cookie(default=None),
):
    destroy_session(db, bookstore_session, response)
    return None


@app.get("/auth/me", response_model=schemas.UserOut, tags=["auth"])
def me(current_user: User = Depends(require_session)):
    return current_user


# ============================================================
# Authors
# ============================================================


@app.get("/authors", response_model=list[schemas.AuthorOut], tags=["authors"])
def read_authors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_authors(db, skip=skip, limit=limit)


@app.get("/authors/{author_id}", response_model=schemas.AuthorWithBooks, tags=["authors"])
def read_author(author_id: int, db: Session = Depends(get_db)):
    db_author = crud.get_author(db, author_id)
    if not db_author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found")
    return db_author


@app.post(
    "/authors",
    response_model=schemas.AuthorOut,
    status_code=status.HTTP_201_CREATED,
    tags=["authors"],
)
def create_author(
    author: schemas.AuthorCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_session),
):
    return crud.create_author(db, author)


@app.put("/authors/{author_id}", response_model=schemas.AuthorOut, tags=["authors"])
def update_author(
    author_id: int,
    changes: schemas.AuthorUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_session),
):
    db_author = crud.get_author(db, author_id)
    if not db_author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found")
    return crud.update_author(db, db_author, changes)


@app.delete("/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["authors"])
def delete_author(
    author_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_session),
):
    db_author = crud.get_author(db, author_id)
    if not db_author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found")
    crud.delete_author(db, db_author)
    return None


# ============================================================
# Books
# ============================================================


@app.get("/books", response_model=list[schemas.BookOut], tags=["books"])
def read_books(skip: int = 0, limit: int = 100, author_id: int | None = None, db: Session = Depends(get_db)):
    return crud.list_books(db, skip=skip, limit=limit, author_id=author_id)


@app.get("/books/{book_id}", response_model=schemas.BookOut, tags=["books"])
def read_book(book_id: int, db: Session = Depends(get_db)):
    db_book = crud.get_book(db, book_id)
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return db_book


@app.post(
    "/books",
    response_model=schemas.BookOut,
    status_code=status.HTTP_201_CREATED,
    tags=["books"],
)
def create_book(
    book: schemas.BookCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_session),
):
    if not crud.get_author(db, book.author_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="author_id does not reference an existing author")
    try:
        return crud.create_book(db, book)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book with this ISBN already exists")


@app.put("/books/{book_id}", response_model=schemas.BookOut, tags=["books"])
def update_book(
    book_id: int,
    changes: schemas.BookUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_session),
):
    db_book = crud.get_book(db, book_id)
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if changes.author_id is not None and not crud.get_author(db, changes.author_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="author_id does not reference an existing author")
    try:
        return crud.update_book(db, db_book, changes)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book with this ISBN already exists")


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["books"])
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_session),
):
    db_book = crud.get_book(db, book_id)
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    crud.delete_book(db, db_book)
    return None


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
