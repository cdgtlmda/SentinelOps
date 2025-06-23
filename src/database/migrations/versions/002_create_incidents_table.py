"""create incidents table

Revision ID: 002_create_incidents_table
Revises: 001_create_rules_table
Create Date: 2025-06-10 11:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002_create_incidents_table"
down_revision = "001_create_rules_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create incidents table
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_number", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "incident_type",
            sa.Enum(
                "unauthorized_access",
                "data_breach",
                "malware",
                "dos_attack",
                "policy_violation",
                "suspicious_activity",
                "other",
                name="securityincidenttype",
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "critical", "high", "medium", "low", "info", name="incidentseverity"
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", "critical", name="priority"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "investigating",
                "contained",
                "remediated",
                "closed",
                "false_positive",
                name="incidentstatus",
            ),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("custom_fields", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.JSON(), nullable=False),
        sa.Column("actors", sa.JSON(), nullable=False),
        sa.Column("assets", sa.JSON(), nullable=False),
        sa.Column("timeline", sa.JSON(), nullable=False),
        sa.Column("analysis", sa.JSON(), nullable=True),
        sa.Column("remediation_actions", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("time_to_detect", sa.Float(), nullable=True),
        sa.Column("time_to_respond", sa.Float(), nullable=True),
        sa.Column("time_to_resolve", sa.Float(), nullable=True),
        sa.Column("parent_incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_incidents", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_incident_id"],
            ["incidents.id"],
            name="fk_incidents_parent_incident_id_incidents",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_incidents"),
        sa.UniqueConstraint("incident_number", name="uq_incidents_incident_number"),
    )

    # Create indexes
    op.create_index("idx_incidents_title", "incidents", ["title"], unique=False)
    op.create_index(
        "idx_incidents_created_at", "incidents", ["created_at"], unique=False
    )
    op.create_index(
        "idx_incidents_updated_at", "incidents", ["updated_at"], unique=False
    )
    op.create_index(
        "idx_incidents_detected_at", "incidents", ["detected_at"], unique=False
    )
    op.create_index(
        "idx_incidents_status_severity",
        "incidents",
        ["status", "severity"],
        unique=False,
    )
    op.create_index(
        "idx_incidents_type_priority",
        "incidents",
        ["incident_type", "priority"],
        unique=False,
    )
    op.create_index(
        "idx_incidents_assigned_status",
        "incidents",
        ["assigned_to", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incidents_incident_number"),
        "incidents",
        ["incident_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incidents_incident_type"), "incidents", ["incident_type"], unique=False
    )
    op.create_index(
        op.f("ix_incidents_severity"), "incidents", ["severity"], unique=False
    )
    op.create_index(
        op.f("ix_incidents_priority"), "incidents", ["priority"], unique=False
    )
    op.create_index(op.f("ix_incidents_status"), "incidents", ["status"], unique=False)
    op.create_index(
        op.f("ix_incidents_external_id"), "incidents", ["external_id"], unique=False
    )
    op.create_index(
        op.f("ix_incidents_assigned_to"), "incidents", ["assigned_to"], unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_incidents_assigned_to"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_external_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_status"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_priority"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_severity"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_incident_type"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_incident_number"), table_name="incidents")
    op.drop_index("idx_incidents_assigned_status", table_name="incidents")
    op.drop_index("idx_incidents_type_priority", table_name="incidents")
    op.drop_index("idx_incidents_status_severity", table_name="incidents")
    op.drop_index("idx_incidents_detected_at", table_name="incidents")
    op.drop_index("idx_incidents_updated_at", table_name="incidents")
    op.drop_index("idx_incidents_created_at", table_name="incidents")
    op.drop_index("idx_incidents_title", table_name="incidents")

    # Drop table
    op.drop_table("incidents")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS incidentstatus")
    op.execute("DROP TYPE IF EXISTS incidentseverity")
    op.execute("DROP TYPE IF EXISTS priority")
    op.execute("DROP TYPE IF EXISTS securityincidenttype")
