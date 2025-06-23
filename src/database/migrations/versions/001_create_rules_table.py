"""create rules table

Revision ID: 001_create_rules_table
Revises:
Create Date: 2025-06-10 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_create_rules_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create rules table
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_number", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "rule_type",
            sa.Enum(
                "query",
                "pattern",
                "threshold",
                "anomaly",
                "correlation",
                "custom",
                name="ruletype",
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum("critical", "high", "medium", "low", "info", name="ruleseverity"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "inactive",
                "testing",
                "disabled",
                "deprecated",
                name="rulestatus",
            ),
            nullable=False,
        ),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("threshold", sa.JSON(), nullable=True),
        sa.Column("correlation", sa.JSON(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("references", sa.JSON(), nullable=False),
        sa.Column("false_positive_rate", sa.Float(), nullable=True),
        sa.Column("actions", sa.JSON(), nullable=False),
        sa.Column("custom_fields", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_executed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("parent_rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_rules", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_rule_id"], ["rules.id"], name="fk_rules_parent_rule_id_rules"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_rules"),
        sa.UniqueConstraint("rule_number", name="uq_rules_rule_number"),
    )

    # Create indexes
    op.create_index("idx_rules_name", "rules", ["name"], unique=False)
    op.create_index("idx_rules_created_at", "rules", ["created_at"], unique=False)
    op.create_index("idx_rules_updated_at", "rules", ["updated_at"], unique=False)
    op.create_index(
        "idx_rules_enabled_status", "rules", ["enabled", "status"], unique=False
    )
    op.create_index(
        "idx_rules_type_severity", "rules", ["rule_type", "severity"], unique=False
    )
    op.create_index(
        op.f("ix_rules_rule_number"), "rules", ["rule_number"], unique=False
    )
    op.create_index(op.f("ix_rules_rule_type"), "rules", ["rule_type"], unique=False)
    op.create_index(op.f("ix_rules_severity"), "rules", ["severity"], unique=False)
    op.create_index(op.f("ix_rules_status"), "rules", ["status"], unique=False)
    op.create_index(op.f("ix_rules_enabled"), "rules", ["enabled"], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_rules_enabled"), table_name="rules")
    op.drop_index(op.f("ix_rules_status"), table_name="rules")
    op.drop_index(op.f("ix_rules_severity"), table_name="rules")
    op.drop_index(op.f("ix_rules_rule_type"), table_name="rules")
    op.drop_index(op.f("ix_rules_rule_number"), table_name="rules")
    op.drop_index("idx_rules_type_severity", table_name="rules")
    op.drop_index("idx_rules_enabled_status", table_name="rules")
    op.drop_index("idx_rules_updated_at", table_name="rules")
    op.drop_index("idx_rules_created_at", table_name="rules")
    op.drop_index("idx_rules_name", table_name="rules")

    # Drop table
    op.drop_table("rules")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS rulestatus")
    op.execute("DROP TYPE IF EXISTS ruleseverity")
    op.execute("DROP TYPE IF EXISTS ruletype")
