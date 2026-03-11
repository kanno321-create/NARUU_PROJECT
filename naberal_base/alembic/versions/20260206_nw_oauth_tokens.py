"""Add nw_oauth_tokens table for LINE WORKS OAuth persistence

Revision ID: 20260206_nw_oauth_tokens
Revises: 20260205_users_table
Create Date: 2026-02-06 21:00:00

This migration adds nw_oauth_tokens table for OAuth token persistence:
- Replaces ephemeral file-based storage (data/api_config.json)
- Survives Railway redeployments
- Supports automatic token refresh
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260206_nw_oauth_tokens'
down_revision = '20260205_users_table'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create nw_oauth_tokens table for LINE WORKS OAuth persistence

    Schema Design:
    - Single-row table (singleton pattern for LINE WORKS config)
    - Stores both API credentials and OAuth tokens
    - Supports automatic token refresh via refresh_token
    """
    op.create_table(
        'nw_oauth_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, comment='Primary key (always 1 for singleton)'),

        # LINE WORKS API Credentials
        sa.Column('client_id', sa.String(255), nullable=True, comment='LINE WORKS Client ID'),
        sa.Column('client_secret', sa.String(255), nullable=True, comment='LINE WORKS Client Secret'),
        sa.Column('service_account', sa.String(255), nullable=True, comment='Service Account email'),
        sa.Column('private_key', sa.Text(), nullable=True, comment='RSA Private Key (PEM format)'),

        # OAuth Tokens
        sa.Column('oauth_access_token', sa.Text(), nullable=True, comment='Current access token'),
        sa.Column('oauth_refresh_token', sa.Text(), nullable=True, comment='Refresh token for auto-renewal'),
        sa.Column('oauth_expires_at', sa.Float(), nullable=True, comment='Token expiry timestamp (Unix epoch)'),
        sa.Column('oauth_user_id', sa.String(255), nullable=True, comment='Authenticated user email'),

        # OAuth State (for CSRF protection during auth flow)
        sa.Column('oauth_state', sa.String(255), nullable=True, comment='OAuth state for CSRF protection'),

        # Timestamps (UTC)
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),

        schema='kis_beta',
        comment='LINE WORKS OAuth tokens and API credentials (singleton table)'
    )

    # Auto-update updated_at trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION kis_beta.update_nw_oauth_tokens_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = timezone('utc', now());
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trigger_nw_oauth_tokens_updated_at
        BEFORE UPDATE ON kis_beta.nw_oauth_tokens
        FOR EACH ROW
        EXECUTE FUNCTION kis_beta.update_nw_oauth_tokens_updated_at();
    """)

    # Initialize singleton row (id=1)
    op.execute("""
        INSERT INTO kis_beta.nw_oauth_tokens (id)
        VALUES (1)
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade():
    """
    Remove nw_oauth_tokens table

    Rollback safe: OAuth tokens will need re-authentication after rollback.
    """
    op.execute("DROP TRIGGER IF EXISTS trigger_nw_oauth_tokens_updated_at ON kis_beta.nw_oauth_tokens;")
    op.execute("DROP FUNCTION IF EXISTS kis_beta.update_nw_oauth_tokens_updated_at();")
    op.drop_table('nw_oauth_tokens', schema='kis_beta')
