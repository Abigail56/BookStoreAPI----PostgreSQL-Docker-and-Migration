"""seed 60 sample authors

Revision ID: c4f2a1d8e7b3
Revises: 961ebac70266
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op


revision: str = "c4f2a1d8e7b3"
down_revision: Union[str, None] = "961ebac70266"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AUTHOR_NAMES = [
    "Amelia Hart",
    "Benjamin Cole",
    "Clara Bennett",
    "Daniel Brooks",
    "Elena Foster",
    "Felix Grant",
    "Grace Morgan",
    "Henry Ellis",
    "Isla Parker",
    "Jack Turner",
    "Katherine Reed",
    "Liam Cooper",
    "Maya Sullivan",
    "Noah Mitchell",
    "Olivia Hayes",
    "Peter Lawson",
    "Quinn Wallace",
    "Ruby Fletcher",
    "Samuel Price",
    "Tessa Armstrong",
    "Uma Dalton",
    "Victor Warren",
    "Wendy Pierce",
    "Xavier Rhodes",
    "Yara Chambers",
    "Zachary Dean",
    "Aisha Reynolds",
    "Caleb Stone",
    "Diana Cross",
    "Ethan Mercer",
    "Florence Webb",
    "George Knight",
    "Hannah Wells",
    "Isaac Bishop",
    "Julia Shaw",
    "Kevin Norris",
    "Laura Hudson",
    "Marcus Flynn",
    "Nora Blake",
    "Oscar Vaughan",
    "Phoebe Carr",
    "Rafael Quinn",
    "Sophie Mason",
    "Theo Harper",
    "Ursula Lane",
    "Violet Marsh",
    "William Kerr",
    "Xenia Ford",
    "Yusuf Bell",
    "Zoey Abbott",
    "Adrian Fox",
    "Bianca Holt",
    "Connor Mills",
    "Delilah Snow",
    "Elliot Nash",
    "Freya Holt",
    "Gideon Moss",
    "Hazel Crane",
    "Ivan Burke",
    "Jasmine Lowe",
    "Kai Monroe",
    "Lydia Park",
]


def upgrade() -> None:
    authors = sa.table(
        "authors",
        sa.column("name", sa.String(length=200)),
        sa.column("bio", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        authors,
        [
            {
                "name": name,
                "bio": f"Sample author profile for {name}.",
                "created_at": datetime.now(UTC),
            }
            for name in AUTHOR_NAMES
        ],
    )


def downgrade() -> None:
    authors = sa.table("authors", sa.column("name", sa.String(length=200)))
    op.execute(
        authors.delete().where(
            authors.c.name.in_(AUTHOR_NAMES),
        ),
    )
