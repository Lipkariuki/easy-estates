from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True)
    property_type = Column(
        Enum("residential", "commercial", "mixed_use", "land", name="property_type_enum"),
        nullable=False,
        server_default="residential",
    )
    address_line_1 = Column(String(255))
    address_line_2 = Column(String(255))
    city = Column(String(120))
    country = Column(String(120))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", foreign_keys=[owner_id])
    manager = relationship("User", foreign_keys=[manager_id])
    assignments = relationship(
        "PropertyManager",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    units = relationship(
        "Unit",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    maintenance_requests = relationship("MaintenanceRequest", back_populates="property")


class PropertyManager(Base):
    __tablename__ = "property_managers"
    __table_args__ = (
        UniqueConstraint("property_id", "user_id", name="uq_property_manager_user"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(
        Enum("owner", "manager", "caretaker", name="property_user_role_enum"),
        nullable=False,
        server_default="manager",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    property = relationship("Property", back_populates="assignments")
    user = relationship("User", back_populates="managed_properties")


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    floor_label = Column(String(50))
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    square_feet = Column(Integer)
    rent_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(
        Enum("available", "occupied", "maintenance", name="unit_status_enum"),
        nullable=False,
        server_default="available",
    )
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    property = relationship("Property", back_populates="units")
    leases = relationship("Lease", back_populates="unit")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="unit")
    audit_logs = relationship("AuditLog", back_populates="unit")


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(50), unique=True, index=True)
    id_number = Column(String(50), unique=True)
    date_of_birth = Column(Date)
    gender = Column(
        Enum("male", "female", "other", "unspecified", name="tenant_gender_enum"),
        nullable=True,
    )
    occupation = Column(String(255))
    emergency_contact_name = Column(String(255))
    emergency_contact_phone = Column(String(50))
    notes = Column(Text)
    kyc_status = Column(
        Enum("pending", "submitted", "approved", "conditional", "declined", name="tenant_kyc_status_enum"),
        nullable=False,
        server_default="pending",
    )
    kyc_score = Column(Integer, nullable=False, server_default=text("0"))
    kyc_submitted_at = Column(DateTime(timezone=True))
    kyc_reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    kyc_reviewed_at = Column(DateTime(timezone=True))
    kyc_override = Column(Boolean, nullable=False, server_default=text("false"))
    kyc_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    leases = relationship("Lease", back_populates="tenant")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="tenant")
    documents = relationship(
        "TenantDocument",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    kyc_sessions = relationship(
        "TenantKycSession",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship("AuditLog", back_populates="tenant")
    kyc_reviewer = relationship("User", foreign_keys=[kyc_reviewed_by_id])
    invites = relationship(
        "TenantInvite",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    kyc_audit_entries = relationship(
        "TenantKycAudit",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )


class TenantDocument(Base):
    __tablename__ = "tenant_documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(
        Enum("id_front", "selfie", "supporting", name="tenant_document_type_enum"),
        nullable=False,
    )
    file_url = Column(String(512), nullable=False)
    status = Column(
        Enum("pending", "accepted", "rejected", name="tenant_document_status_enum"),
        nullable=False,
        server_default="pending",
    )
    score_value = Column(Integer, nullable=False, server_default=text("0"))
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    notes = Column(Text)

    tenant = relationship("Tenant", back_populates="documents")
    reviewer = relationship("User")


class TenantKycSession(Base):
    __tablename__ = "tenant_kyc_sessions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), nullable=False, unique=True, index=True)
    status = Column(
        Enum("open", "completed", "expired", "cancelled", name="tenant_kyc_session_status_enum"),
        nullable=False,
        server_default="open",
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    tenant = relationship("Tenant", back_populates="kyc_sessions")


class Lease(Base):
    __tablename__ = "leases"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    rent_amount = Column(Numeric(12, 2), nullable=False)
    deposit_amount = Column(Numeric(12, 2))
    payment_day = Column(Integer)
    status = Column(
        Enum("draft", "active", "terminated", "expired", name="lease_status_enum"),
        nullable=False,
        server_default="draft",
    )
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    unit = relationship("Unit", back_populates="leases")
    tenant = relationship("Tenant", back_populates="leases")
    invoices = relationship(
        "RentInvoice",
        back_populates="lease",
        cascade="all, delete-orphan",
    )


class RentInvoice(Base):
    __tablename__ = "rent_invoices"

    id = Column(Integer, primary_key=True, index=True)
    lease_id = Column(Integer, ForeignKey("leases.id", ondelete="CASCADE"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount_due = Column(Numeric(12, 2), nullable=False)
    amount_paid = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    status = Column(
        Enum("pending", "partial", "paid", "overdue", name="invoice_status_enum"),
        nullable=False,
        server_default="pending",
    )
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lease = relationship("Lease", back_populates="invoices")
    payments = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("rent_invoices.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    paid_on = Column(Date, nullable=False)
    method = Column(
        Enum("cash", "mobile_money", "bank_transfer", "cheque", "other", name="payment_method_enum"),
        nullable=False,
        server_default="cash",
    )
    reference = Column(String(120))
    received_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoice = relationship("RentInvoice", back_populates="payments")
    received_by = relationship("User")


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="SET NULL"))
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(
        Enum("low", "medium", "high", "urgent", name="maint_priority_enum"),
        nullable=False,
        server_default="medium",
    )
    status = Column(
        Enum("open", "in_progress", "closed", name="maint_status_enum"),
        nullable=False,
        server_default="open",
    )
    reported_on = Column(Date, nullable=False)
    resolved_on = Column(Date)
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    property = relationship("Property", back_populates="maintenance_requests")
    unit = relationship("Unit", back_populates="maintenance_requests")
    tenant = relationship("Tenant", back_populates="maintenance_requests")
    assigned_to = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    action = Column(
        Enum(
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
        nullable=False,
    )
    entity_type = Column(String(120), nullable=False)
    entity_id = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    actor = relationship("User", back_populates="audit_logs")
    tenant = relationship("Tenant", back_populates="audit_logs")
    property = relationship("Property")
    unit = relationship("Unit", back_populates="audit_logs")


class TenantKycAudit(Base):
    __tablename__ = "tenant_kyc_audit"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50))
    new_status = Column(String(50))
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="kyc_audit_entries")
    changed_by = relationship("User")


class TenantInvite(Base):
    __tablename__ = "tenant_invites"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    token = Column(String(64), nullable=False, unique=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=False)

    tenant = relationship("Tenant", back_populates="invites")


class UserVerificationToken(Base):
    __tablename__ = "user_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="verification_tokens")
