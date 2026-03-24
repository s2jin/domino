"""Add chat_session and chat_message tables

Revision ID: b1c2d3e4f567
Revises: 758034ba1a89
Create Date: 2026-03-23

"""
from alembic import op
import sqlalchemy as sa

revision = 'b1c2d3e4f567'
down_revision = '758034ba1a89'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'chat_session',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False, server_default='New Chat'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
    )

    op.create_table(
        'chat_message',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('chat_session.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', 'think', 'tool', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('chat_message')
    op.drop_table('chat_session')
    op.execute("DROP TYPE IF EXISTS messagerole")
