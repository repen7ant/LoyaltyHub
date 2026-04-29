"""add_offer_type_and_target_product_id

Revision ID: 89b07c742263
Revises: d3b679bf919a
Create Date: 2026-04-29 17:19:27.531453

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "89b07c742263"
down_revision: Union[str, Sequence[str], None] = "d3b679bf919a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Явно создаем тип ENUM в PostgreSQL
    offer_type_enum = postgresql.ENUM("PARTNER", "ECOSYSTEM", name="offertype")
    offer_type_enum.create(op.get_bind())

    # 2. Добавляем колонки. Важно указать server_default, чтобы существующие записи
    # в таблице не вызвали ошибку NOT NULL
    op.add_column(
        "offers",
        sa.Column(
            "offer_type", offer_type_enum, server_default="PARTNER", nullable=False
        ),
    )
    op.add_column(
        "offers", sa.Column("target_product_id", sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    # 1. Удаляем колонки
    op.drop_column("offers", "target_product_id")
    op.drop_column("offers", "offer_type")

    # 2. Явно удаляем тип ENUM из PostgreSQL
    offer_type_enum = postgresql.ENUM("PARTNER", "ECOSYSTEM", name="offertype")
    offer_type_enum.drop(op.get_bind())
