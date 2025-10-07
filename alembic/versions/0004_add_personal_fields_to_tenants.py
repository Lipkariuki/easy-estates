"""Add personal fields to tenants

Revision ID: 0004_add_personal_fields
Revises: 0003_property_ui_fields
Create Date: 2025-10-02 15:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004_add_personal_fields"
down_revision = "0002_mvp_estate_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    gender_enum = sa.Enum("male", "female", "other", "unspecified", name="tenant_gender_enum")
    bind = op.get_bind()
    gender_enum.create(bind, checkfirst=True)

    op.add_column("tenants", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("tenants", sa.Column("gender", gender_enum, nullable=True))
    op.add_column("tenants", sa.Column("occupation", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "occupation")
    op.drop_column("tenants", "gender")
    op.drop_column("tenants", "date_of_birth")

    gender_enum = sa.Enum("male", "female", "other", "unspecified", name="tenant_gender_enum")
    bind = op.get_bind()
    gender_enum.drop(bind, checkfirst=True)
