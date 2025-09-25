from alembic import op
import sqlalchemy as sa

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String, nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String, nullable=False),
        sa.Column('role', sa.Enum('owner','manager','caretaker','viewer', name='user_roles'), nullable=False, server_default='owner'),
        sa.Column('active', sa.Boolean, server_default=sa.text('true')),
    )

def downgrade():
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS user_roles")
