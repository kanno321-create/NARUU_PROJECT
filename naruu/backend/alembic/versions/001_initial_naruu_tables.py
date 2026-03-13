"""Initial NARUU tables — all 13 ORM models.

Revision ID: 001_initial_naruu
Revises: (none — first migration for naruu schema)
Create Date: 2026-03-13

Creates tables in FK-safe order:
  1. users, customers, partners, packages, goods, contents  (no FKs to other naruu tables)
  2. reservations  (FK -> customers, packages, partners, users)
  3. orders        (FK -> customers, packages, reservations)
  4. expenses      (FK -> users)
  5. reviews       (FK -> customers, partners)
  6. tour_routes   (FK -> customers, packages, users)
  7. line_messages  (FK -> customers)
  8. ai_conversations (FK -> users)

Enum types are created explicitly before tables that reference them.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "001_initial_naruu"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # Enum types
    # ---------------------------------------------------------------
    user_role = sa.Enum("admin", "manager", "staff", name="user_role", create_type=True)
    package_category = sa.Enum("medical", "tourism", "combo", "goods", name="package_category", create_type=True)
    currency_type = sa.Enum("JPY", "KRW", name="currency_type", create_type=True)
    goods_category = sa.Enum("bag", "accessory", "souvenir", name="goods_category", create_type=True)
    content_series = sa.Enum("DaeguTour", "JCouple", "Medical", "Brochure", name="content_series", create_type=True)
    content_status = sa.Enum("draft", "review", "approved", "published", "rejected", name="content_status", create_type=True)
    content_platform = sa.Enum("youtube", "instagram", "tiktok", name="content_platform", create_type=True)
    partner_type = sa.Enum("hospital", "clinic", "restaurant", "hotel", "shop", name="partner_type", create_type=True)
    reservation_status = sa.Enum("pending", "confirmed", "completed", "cancelled", name="reservation_status", create_type=True)
    reservation_type = sa.Enum("medical", "tourism", "restaurant", "goods", name="reservation_type", create_type=True)
    payment_status = sa.Enum("pending", "paid", "refunded", "cancelled", name="payment_status", create_type=True)
    review_platform = sa.Enum("google", "instagram", "line", "naver", "tabelog", name="review_platform", create_type=True)
    route_status = sa.Enum("draft", "published", "archived", name="route_status", create_type=True)
    message_direction = sa.Enum("in", "out", name="message_direction", create_type=True)
    message_type = sa.Enum("text", "image", "template", "sticker", name="message_type", create_type=True)
    conversation_context = sa.Enum("chat", "query", "content", "translation", name="conversation_context", create_type=True)

    # ---------------------------------------------------------------
    # 1. users
    # ---------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name_ko", sa.String(100), nullable=False),
        sa.Column("name_ja", sa.String(100), nullable=True),
        sa.Column("role", user_role, nullable=False, server_default="staff"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---------------------------------------------------------------
    # 2. customers
    # ---------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name_ja", sa.String(100), nullable=False),
        sa.Column("name_ko", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("line_user_id", sa.String(100), unique=True, index=True, nullable=True),
        sa.Column("nationality", sa.String(50), nullable=False, server_default="JP", index=True),
        sa.Column("visa_type", sa.String(50), nullable=True),
        sa.Column("first_visit_date", sa.Date(), nullable=True),
        sa.Column("preferred_language", sa.String(10), nullable=False, server_default="ja"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.String(50)), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---------------------------------------------------------------
    # 3. partners
    # ---------------------------------------------------------------
    op.create_table(
        "partners",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name_ko", sa.String(200), nullable=False),
        sa.Column("name_ja", sa.String(200), nullable=True),
        sa.Column("type", partner_type, nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("contact_person", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("commission_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("contract_start", sa.Date(), nullable=True),
        sa.Column("contract_end", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---------------------------------------------------------------
    # 4. packages
    # ---------------------------------------------------------------
    op.create_table(
        "packages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name_ja", sa.String(200), nullable=False),
        sa.Column("name_ko", sa.String(200), nullable=False),
        sa.Column("description_ja", sa.Text(), nullable=True),
        sa.Column("description_ko", sa.Text(), nullable=True),
        sa.Column("category", package_category, nullable=False),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", currency_type, nullable=False, server_default="JPY"),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("includes", sa.ARRAY(sa.String(200)), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---------------------------------------------------------------
    # 5. goods
    # ---------------------------------------------------------------
    op.create_table(
        "goods",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name_ja", sa.String(200), nullable=False),
        sa.Column("name_ko", sa.String(200), nullable=False),
        sa.Column("description_ja", sa.Text(), nullable=True),
        sa.Column("description_ko", sa.Text(), nullable=True),
        sa.Column("category", goods_category, nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_urls", sa.ARRAY(sa.String(500)), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---------------------------------------------------------------
    # 6. contents
    # ---------------------------------------------------------------
    op.create_table(
        "contents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("series", content_series, nullable=False),
        sa.Column("script_ja", sa.Text(), nullable=True),
        sa.Column("script_ko", sa.Text(), nullable=True),
        sa.Column("status", content_status, nullable=False, server_default="draft", index=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("platform", content_platform, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("performance_metrics", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_contents_created_at", "contents", ["created_at"])

    # ---------------------------------------------------------------
    # 7. reservations (FK -> customers, packages, partners, users)
    # ---------------------------------------------------------------
    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("packages.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("reservation_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", reservation_status, nullable=False, server_default="pending", index=True),
        sa.Column("type", reservation_type, nullable=False, index=True),
        sa.Column("notes_ja", sa.Text(), nullable=True),
        sa.Column("notes_ko", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---------------------------------------------------------------
    # 8. orders (FK -> customers, packages, reservations)
    # ---------------------------------------------------------------
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("packages.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("reservation_id", sa.Integer(), sa.ForeignKey("reservations.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", currency_type, nullable=False, server_default="JPY"),
        sa.Column("payment_status", payment_status, nullable=False, server_default="pending", index=True),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("commission_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("commission_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_orders_created_at", "orders", ["created_at"])

    # ---------------------------------------------------------------
    # 9. expenses (FK -> users)
    # ---------------------------------------------------------------
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("vendor_name", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", currency_type, nullable=False, server_default="KRW"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("receipt_url", sa.String(500), nullable=True),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---------------------------------------------------------------
    # 10. reviews (FK -> customers, partners)
    # ---------------------------------------------------------------
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("platform", review_platform, nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("content_ja", sa.Text(), nullable=True),
        sa.Column("content_ko", sa.Text(), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---------------------------------------------------------------
    # 11. tour_routes (FK -> customers, packages, users)
    # ---------------------------------------------------------------
    op.create_table(
        "tour_routes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name_ja", sa.String(200), nullable=False),
        sa.Column("name_ko", sa.String(200), nullable=False),
        sa.Column("description_ja", sa.Text(), nullable=True),
        sa.Column("description_ko", sa.Text(), nullable=True),
        sa.Column("waypoints", JSONB, nullable=True),
        sa.Column("route_data", JSONB, nullable=True),
        sa.Column("status", route_status, nullable=False, server_default="draft"),
        sa.Column("total_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("total_distance_km", sa.Numeric(8, 2), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.String(100)), nullable=True),
        sa.Column("is_template", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("packages.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ---------------------------------------------------------------
    # 12. line_messages (FK -> customers)
    # ---------------------------------------------------------------
    op.create_table(
        "line_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("line_user_id", sa.String(100), nullable=False, index=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("direction", message_direction, nullable=False, index=True),
        sa.Column("message_type", message_type, nullable=False, server_default="text"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_line_messages_created_at", "line_messages", ["created_at"])

    # ---------------------------------------------------------------
    # 13. ai_conversations (FK -> users)
    # ---------------------------------------------------------------
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("context", conversation_context, nullable=False),
        sa.Column("messages", JSONB, nullable=False),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop tables in reverse FK order, then enum types."""

    # Tables with FKs first (reverse creation order)
    op.drop_table("ai_conversations")
    op.drop_table("line_messages")
    op.drop_table("tour_routes")
    op.drop_table("reviews")
    op.drop_table("expenses")
    op.drop_table("orders")
    op.drop_table("reservations")

    # Independent tables
    op.drop_table("contents")
    op.drop_table("goods")
    op.drop_table("packages")
    op.drop_table("partners")
    op.drop_table("customers")
    op.drop_table("users")

    # Enum types
    sa.Enum(name="conversation_context").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="message_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="message_direction").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="route_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="review_platform").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reservation_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reservation_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="partner_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="content_platform").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="content_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="content_series").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="goods_category").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="currency_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="package_category").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
