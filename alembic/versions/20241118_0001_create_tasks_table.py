"""create tasks table

Revision ID: 20241118_0001
Revises:
Create Date: 2024-11-18 00:01:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20241118_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    task_priority = sa.Enum("LOW", "MEDIUM", "HIGH", name="task_priority")
    task_status = sa.Enum(
        "NEW",
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        name="task_status",
    )
    task_priority.create(op.get_bind(), checkfirst=True)
    task_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", task_priority, nullable=False),
        sa.Column("status", task_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_tasks_status_priority",
        "tasks",
        ["status", "priority"],
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_status_priority", table_name="tasks")
    op.drop_table("tasks")
    task_priority = sa.Enum("LOW", "MEDIUM", "HIGH", name="task_priority")
    task_status = sa.Enum(
        "NEW",
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        name="task_status",
    )
    task_status.drop(op.get_bind(), checkfirst=True)
    task_priority.drop(op.get_bind(), checkfirst=True)

