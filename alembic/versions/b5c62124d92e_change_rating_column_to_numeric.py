"""Change rating column to numeric

Revision ID: b5c62124d92e
Revises: a795ef55480c
Create Date: 2025-01-01 18:45:56.127676

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b5c62124d92e"
down_revision: Union[str, None] = "a795ef55480c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Зміна типу колонки 'rating' в таблиці 'photos' на DECIMAL(5,2)
    op.alter_column(
        "photos",
        "rating",
        type_=sa.Numeric(precision=5, scale=2),
        existing_type=sa.Integer(),
    )
    # ### end Alembic commands ###


def downgrade():
    # Повернення типу колонки на Integer у разі відкату міграції
    op.alter_column(
        "photos",
        "rating",
        type_=sa.Integer(),
        existing_type=sa.Numeric(precision=5, scale=2),
    )
    # ### end Alembic commands ###
