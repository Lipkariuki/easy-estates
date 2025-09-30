"""Add core estate management tables

Revision ID: 0002_mvp_estate_tables
Revises: 0001_init
Create Date: 2025-02-15
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_mvp_estate_tables"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    enums = {
        "property_type_enum": sa.Enum(
            "residential", "commercial", "mixed_use", "land", name="property_type_enum"
        ),
        "unit_status_enum": sa.Enum(
            "available", "occupied", "maintenance", name="unit_status_enum"
        ),
        "tenant_kyc_status_enum": sa.Enum(
            "pending", "submitted", "approved", "conditional", "declined", name="tenant_kyc_status_enum"
        ),
        "tenant_document_type_enum": sa.Enum(
            "id_front", "selfie", "supporting", name="tenant_document_type_enum"
        ),
        "tenant_document_status_enum": sa.Enum(
            "pending", "accepted", "rejected", name="tenant_document_status_enum"
        ),
        "tenant_kyc_session_status_enum": sa.Enum(
            "open", "completed", "expired", "cancelled", name="tenant_kyc_session_status_enum"
        ),
        "lease_status_enum": sa.Enum(
            "draft", "active", "terminated", "expired", name="lease_status_enum"
        ),
        "invoice_status_enum": sa.Enum(
            "pending", "partial", "paid", "overdue", name="invoice_status_enum"
        ),
        "payment_method_enum": sa.Enum(
            "cash", "mobile_money", "bank_transfer", "cheque", "other", name="payment_method_enum"
        ),
        "maint_priority_enum": sa.Enum(
            "low", "medium", "high", "urgent", name="maint_priority_enum"
        ),
        "maint_status_enum": sa.Enum(
            "open", "in_progress", "closed", name="maint_status_enum"
        ),
        "property_user_role_enum": sa.Enum(
            "owner", "manager", "caretaker", name="property_user_role_enum"
        ),
        "audit_action_enum": sa.Enum(
            "create",
            "update",
            "approve",
            "decline",
            "override",
            "invite",
            "login",
            "other",
            name="audit_action_enum",
        ),
    }

    for enum in enums.values():
        enum.create(bind, checkfirst=True)

    # Tenants
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True, unique=True),
        sa.Column("phone", sa.String(length=50), nullable=True, unique=True),
        sa.Column("id_number", sa.String(length=50), nullable=True, unique=True),
        sa.Column("emergency_contact_name", sa.String(length=255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "kyc_status",
            enums["tenant_kyc_status_enum"],
            nullable=False,
            server_default="pending",
        ),
        sa.Column("kyc_score", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("kyc_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kyc_reviewed_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("kyc_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kyc_override", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("kyc_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Properties
    op.create_table(
        "properties",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=True, unique=True),
        sa.Column(
            "property_type",
            enums["property_type_enum"],
            nullable=False,
            server_default="residential",
        ),
        sa.Column("address_line_1", sa.String(length=255), nullable=True),
        sa.Column("address_line_2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("manager_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Property managers
    op.create_table(
        "property_managers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "property_id",
            sa.Integer,
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "role",
            enums["property_user_role_enum"],
            nullable=False,
            server_default="manager",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("property_id", "user_id", name="uq_property_manager_user"),
    )

    # Units
    op.create_table(
        "units",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "property_id",
            sa.Integer,
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("floor_label", sa.String(length=50), nullable=True),
        sa.Column("bedrooms", sa.Integer, nullable=True),
        sa.Column("bathrooms", sa.Integer, nullable=True),
        sa.Column("square_feet", sa.Integer, nullable=True),
        sa.Column("rent_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "status",
            enums["unit_status_enum"],
            nullable=False,
            server_default="available",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Tenant KYC documents
    op.create_table(
        "tenant_documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("doc_type", enums["tenant_document_type_enum"], nullable=False),
        sa.Column("file_url", sa.String(length=512), nullable=False),
        sa.Column(
            "status",
            enums["tenant_document_status_enum"],
            nullable=False,
            server_default="pending",
        ),
        sa.Column("score_value", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("reviewed_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # Tenant KYC sessions
    op.create_table(
        "tenant_kyc_sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=64), nullable=False, unique=True),
        sa.Column(
            "status",
            enums["tenant_kyc_session_status_enum"],
            nullable=False,
            server_default="open",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Tenant invites (for onboarding emails)
    op.create_table(
        "tenant_invites",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False, unique=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Tenant KYC audit trail
    op.create_table(
        "tenant_kyc_audit",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("previous_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=True),
        sa.Column("changed_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Leases
    op.create_table(
        "leases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "unit_id",
            sa.Integer,
            sa.ForeignKey("units.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("rent_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("deposit_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("payment_day", sa.Integer, nullable=True),
        sa.Column("status", enums["lease_status_enum"], nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Rent invoices
    op.create_table(
        "rent_invoices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "lease_id",
            sa.Integer,
            sa.ForeignKey("leases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("amount_due", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("status", enums["invoice_status_enum"], nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "invoice_id",
            sa.Integer,
            sa.ForeignKey("rent_invoices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("method", enums["payment_method_enum"], nullable=False, server_default="cash"),
        sa.Column("reference", sa.String(length=120), nullable=True),
        sa.Column("received_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Maintenance requests
    op.create_table(
        "maintenance_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "property_id",
            sa.Integer,
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("unit_id", sa.Integer, sa.ForeignKey("units.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", enums["maint_priority_enum"], nullable=False, server_default="medium"),
        sa.Column("status", enums["maint_status_enum"], nullable=False, server_default="open"),
        sa.Column("reported_on", sa.Date(), nullable=False),
        sa.Column("resolved_on", sa.Date(), nullable=True),
        sa.Column("assigned_to_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Audit logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("property_id", sa.Integer, sa.ForeignKey("properties.id"), nullable=True),
        sa.Column("unit_id", sa.Integer, sa.ForeignKey("units.id"), nullable=True),
        sa.Column("action", enums["audit_action_enum"], nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # User verification tokens (email verification)
    op.create_table(
        "user_verification_tokens",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Indexes
    op.create_index("ix_tenants_email", "tenants", ["email"], unique=False)
    op.create_index("ix_tenants_phone", "tenants", ["phone"], unique=False)
    op.create_index("ix_tenants_id_number", "tenants", ["id_number"], unique=False)
    op.create_index("ix_units_property_id_name", "units", ["property_id", "name"], unique=True)
    op.create_index(
        "ix_leases_unit_tenant_status",
        "leases",
        ["unit_id", "tenant_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_rent_invoices_lease_period",
        "rent_invoices",
        ["lease_id", "period_start"],
        unique=True,
    )
    op.create_index(
        "ix_tenant_documents_tenant_type",
        "tenant_documents",
        ["tenant_id", "doc_type"],
        unique=False,
    )
    op.create_index(
        "ix_tenant_kyc_sessions_token",
        "tenant_kyc_sessions",
        ["token"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_tenant_kyc_sessions_token", table_name="tenant_kyc_sessions")
    op.drop_index("ix_tenant_documents_tenant_type", table_name="tenant_documents")
    op.drop_index("ix_rent_invoices_lease_period", table_name="rent_invoices")
    op.drop_index("ix_leases_unit_tenant_status", table_name="leases")
    op.drop_index("ix_units_property_id_name", table_name="units")
    op.drop_index("ix_tenants_id_number", table_name="tenants")
    op.drop_index("ix_tenants_phone", table_name="tenants")
    op.drop_index("ix_tenants_email", table_name="tenants")

    op.drop_table("user_verification_tokens")
    op.drop_table("audit_logs")
    op.drop_table("maintenance_requests")
    op.drop_table("payments")
    op.drop_table("rent_invoices")
    op.drop_table("leases")
    op.drop_table("tenant_kyc_audit")
    op.drop_table("tenant_invites")
    op.drop_table("tenant_kyc_sessions")
    op.drop_table("tenant_documents")
    op.drop_table("units")
    op.drop_table("property_managers")
    op.drop_table("properties")
    op.drop_table("tenants")

    bind = op.get_bind()
    for enum_name in [
        "audit_action_enum",
        "property_user_role_enum",
        "maint_status_enum",
        "maint_priority_enum",
        "payment_method_enum",
        "invoice_status_enum",
        "lease_status_enum",
        "tenant_kyc_session_status_enum",
        "tenant_document_status_enum",
        "tenant_document_type_enum",
        "tenant_kyc_status_enum",
        "unit_status_enum",
        "property_type_enum",
    ]:
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
