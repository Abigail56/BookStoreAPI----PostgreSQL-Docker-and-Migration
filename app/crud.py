from sqlalchemy.orm import Session

from app import models, schemas

# ---------- Author ----------


def get_author(db: Session, author_id: int) -> models.Author | None:
    return db.query(models.Author).filter(models.Author.id == author_id).first()


def list_authors(db: Session, skip: int = 0, limit: int = 100) -> list[models.Author]:
    return db.query(models.Author).offset(skip).limit(limit).all()


def create_author(db: Session, author: schemas.AuthorCreate) -> models.Author:
    db_author = models.Author(name=author.name, bio=author.bio)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author


def update_author(db: Session, db_author: models.Author, changes: schemas.AuthorUpdate) -> models.Author:
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(db_author, field, value)
    db.commit()
    db.refresh(db_author)
    return db_author


def delete_author(db: Session, db_author: models.Author) -> None:
    db.delete(db_author)
    db.commit()


# ---------- Book ----------


def get_book(db: Session, book_id: int) -> models.Book | None:
    return db.query(models.Book).filter(models.Book.id == book_id).first()


def list_books(db: Session, skip: int = 0, limit: int = 100, author_id: int | None = None) -> list[models.Book]:
    query = db.query(models.Book)
    if author_id is not None:
        query = query.filter(models.Book.author_id == author_id)
    return query.offset(skip).limit(limit).all()


def create_book(db: Session, book: schemas.BookCreate) -> models.Book:
    db_book = models.Book(
        title=book.title,
        isbn=book.isbn,
        published_year=book.published_year,
        author_id=book.author_id,
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def update_book(db: Session, db_book: models.Book, changes: schemas.BookUpdate) -> models.Book:
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(db_book, field, value)
    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, db_book: models.Book) -> None:
    db.delete(db_book)
    db.commit()
