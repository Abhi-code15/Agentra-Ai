"""add_multi_tenant_policies_and_claims

Revision ID: 8488b8195247
Revises: 56643401829d
Create Date: 2026-11-19 00:58:44.799166

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8488b8195247'
down_revision: Union[str, Sequence[str], None] = '56643401829d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')", name='ck_organizations_status'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_organizations_slug'),
    )
    op.create_index('idx_organizations_slug', 'organizations', ['slug'], unique=False)
    op.create_index('idx_organizations_status', 'organizations', ['status'], unique=False)

    # 2. Departments
    op.create_table(
        'departments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_departments_organization', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'name', name='uq_departments_org_name'),
    )
    op.create_index('idx_departments_org_id', 'departments', ['organization_id'], unique=False)

    # 3. Organization Members
    op.create_table(
        'organization_members',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='EMPLOYEE'),
        sa.Column('employee_code', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('ORG_ADMIN', 'POLICY_MANAGER', 'REVIEWER', 'AUDITOR', 'EMPLOYEE')", name='ck_org_members_role'),
        sa.CheckConstraint("status IN ('ACTIVE', 'INVITED', 'SUSPENDED')", name='ck_org_members_status'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], name='fk_org_members_department', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_org_members_organization', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_org_members_user', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_members_user_org'),
    )
    op.create_index('idx_org_members_org_user', 'organization_members', ['organization_id', 'user_id'], unique=False)
    op.create_index('idx_org_members_role', 'organization_members', ['organization_id', 'role'], unique=False)

    # 4. Policies
    op.create_table(
        'policies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("category IN ('EXPENSE', 'LEAVE', 'TRAVEL', 'PROCUREMENT', 'HR', 'GENERAL')", name='ck_policies_category'),
        sa.CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'ARCHIVED')", name='ck_policies_status'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_policies_created_by', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], name='fk_policies_department', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_policies_organization', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_policies_org_cat', 'policies', ['organization_id', 'category'], unique=False)
    op.create_index('idx_policies_status', 'policies', ['status'], unique=False)

    # 5. Policy Versions
    op.create_table(
        'policy_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('policy_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('effective_from', sa.Date(), nullable=True),
        sa.Column('effective_until', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('extracted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('DRAFT', 'PROCESSING', 'PENDING_APPROVAL', 'APPROVED', 'ACTIVE', 'SUPERSEDED', 'ARCHIVED')", name='ck_policy_versions_status'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name='fk_policy_versions_approved_by', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name='fk_policy_versions_document', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], name='fk_policy_versions_policy', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('policy_id', 'version_number', name='uq_policy_versions_policy_num'),
    )
    op.create_index('idx_policy_versions_dates', 'policy_versions', ['effective_from', 'effective_until'], unique=False)
    op.create_index('idx_policy_versions_status', 'policy_versions', ['status'], unique=False)

    # 6. Policy Rules
    op.create_table(
        'policy_rules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('policy_version_id', sa.UUID(), nullable=False),
        sa.Column('rule_code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('rule_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('source_reference', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('extraction_confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='UNVERIFIED'),
        sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("approval_status IN ('PENDING', 'APPROVED', 'REJECTED')", name='ck_policy_rules_approval'),
        sa.CheckConstraint("category IN ('ELIGIBILITY', 'LIMIT', 'DOCUMENTATION', 'APPROVAL', 'TIMELINESS', 'RESTRICTION')", name='ck_policy_rules_category'),
        sa.CheckConstraint("rule_type IN ('NUMERIC_LIMIT', 'CATEGORICAL_ALLOWED', 'CATEGORICAL_DISALLOWED', 'MANDATORY_DOCUMENTATION', 'SUBMISSION_DEADLINE', 'APPROVAL_TIER')", name='ck_policy_rules_type'),
        sa.CheckConstraint("verification_status IN ('UNVERIFIED', 'VERIFIED', 'MODIFIED')", name='ck_policy_rules_verification'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name='fk_policy_rules_approved_by', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_policy_rules_created_by', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['policy_version_id'], ['policy_versions.id'], name='fk_policy_rules_version', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('policy_version_id', 'rule_code', name='uq_policy_rules_version_code'),
    )
    op.create_index('idx_policy_rules_status', 'policy_rules', ['approval_status', 'verification_status'], unique=False)
    op.create_index('idx_policy_rules_version', 'policy_rules', ['policy_version_id'], unique=False)

    # 7. Claims
    op.create_table(
        'claims',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('employee_id', sa.UUID(), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=True),
        sa.Column('policy_id', sa.UUID(), nullable=True),
        sa.Column('policy_version_id', sa.UUID(), nullable=True),
        sa.Column('analysis_run_id', sa.UUID(), nullable=True),
        sa.Column('claim_type', sa.String(length=50), nullable=False, server_default='EXPENSE'),
        sa.Column('claim_number', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SUBMITTED'),
        sa.Column('expense_date', sa.Date(), nullable=True),
        sa.Column('submission_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("claim_type IN ('EXPENSE', 'LEAVE', 'TRAVEL', 'PROCUREMENT')", name='ck_claims_type'),
        sa.CheckConstraint("status IN ('DRAFT', 'SUBMITTED', 'EVALUATING', 'EVALUATED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'REVISION_REQUESTED')", name='ck_claims_status'),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], name='fk_claims_analysis_run', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], name='fk_claims_department', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['employee_id'], ['users.id'], name='fk_claims_employee', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_claims_organization', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], name='fk_claims_policy', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['policy_version_id'], ['policy_versions.id'], name='fk_claims_policy_version', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_number', name='uq_claims_claim_number'),
    )
    op.create_index('idx_claims_employee', 'claims', ['employee_id'], unique=False)
    op.create_index('idx_claims_number', 'claims', ['claim_number'], unique=False)
    op.create_index('idx_claims_org_status', 'claims', ['organization_id', 'status'], unique=False)

    # 8. Claim Line Items
    op.create_table(
        'claim_line_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('claim_id', sa.UUID(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('transaction_date', sa.Date(), nullable=True),
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], name='fk_claim_line_items_claim', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_claim_items_cat', 'claim_line_items', ['category'], unique=False)
    op.create_index('idx_claim_items_claim_id', 'claim_line_items', ['claim_id'], unique=False)

    # 9. Claim Documents
    op.create_table(
        'claim_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('claim_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False, server_default='RECEIPT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], name='fk_claim_docs_claim', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name='fk_claim_docs_document', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_id', 'document_id', name='uq_claim_documents_claim_doc'),
    )
    op.create_index('idx_claim_docs_claim_id', 'claim_documents', ['claim_id'], unique=False)
    op.create_index('idx_claim_docs_doc_id', 'claim_documents', ['document_id'], unique=False)

    # 10. Update existing tables for multi-tenancy & claim associations
    # documents
    op.add_column('documents', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('documents', sa.Column('document_type', sa.String(length=50), nullable=False, server_default='POLICY_DOCUMENT'))
    op.create_index('idx_documents_org_id', 'documents', ['organization_id'], unique=False)
    op.create_index('idx_documents_type', 'documents', ['document_type'], unique=False)
    op.create_foreign_key('fk_documents_organization', 'documents', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # analysis_runs
    op.add_column('analysis_runs', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('analysis_runs', sa.Column('claim_id', sa.UUID(), nullable=True))
    op.alter_column('analysis_runs', 'document_id', existing_type=sa.UUID(), nullable=True)
    op.create_index('idx_analysis_runs_claim_id', 'analysis_runs', ['claim_id'], unique=False)
    op.create_index('idx_analysis_runs_org_id', 'analysis_runs', ['organization_id'], unique=False)
    op.create_foreign_key('fk_analysis_runs_organization', 'analysis_runs', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_analysis_runs_claim', 'analysis_runs', 'claims', ['claim_id'], ['id'], ondelete='SET NULL')

    # findings
    op.add_column('findings', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('findings', sa.Column('claim_id', sa.UUID(), nullable=True))
    op.add_column('findings', sa.Column('policy_rule_id', sa.UUID(), nullable=True))
    op.alter_column('findings', 'analysis_run_id', existing_type=sa.UUID(), nullable=True)
    op.create_index('idx_findings_claim_id', 'findings', ['claim_id'], unique=False)
    op.create_index('idx_findings_org_id', 'findings', ['organization_id'], unique=False)
    op.create_index('idx_findings_policy_rule_id', 'findings', ['policy_rule_id'], unique=False)
    op.create_foreign_key('fk_findings_organization', 'findings', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_findings_claim', 'findings', 'claims', ['claim_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_findings_policy_rule', 'findings', 'policy_rules', ['policy_rule_id'], ['id'], ondelete='SET NULL')

    # review_tasks
    op.add_column('review_tasks', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('review_tasks', sa.Column('claim_id', sa.UUID(), nullable=True))
    op.alter_column('review_tasks', 'finding_id', existing_type=sa.UUID(), nullable=True)
    op.create_index('idx_review_tasks_claim_id', 'review_tasks', ['claim_id'], unique=False)
    op.create_index('idx_review_tasks_org_id', 'review_tasks', ['organization_id'], unique=False)
    op.create_foreign_key('fk_review_tasks_organization', 'review_tasks', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_review_tasks_claim', 'review_tasks', 'claims', ['claim_id'], ['id'], ondelete='CASCADE')

    # audit_events
    op.add_column('audit_events', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.create_index('idx_audit_events_org_id', 'audit_events', ['organization_id'], unique=False)
    op.create_foreign_key('fk_audit_events_organization', 'audit_events', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop added constraints and columns from existing tables
    op.drop_constraint('fk_audit_events_organization', 'audit_events', type_='foreignkey')
    op.drop_index('idx_audit_events_org_id', table_name='audit_events')
    op.drop_column('audit_events', 'organization_id')

    op.drop_constraint('fk_review_tasks_claim', 'review_tasks', type_='foreignkey')
    op.drop_constraint('fk_review_tasks_organization', 'review_tasks', type_='foreignkey')
    op.drop_index('idx_review_tasks_org_id', table_name='review_tasks')
    op.drop_index('idx_review_tasks_claim_id', table_name='review_tasks')
    op.alter_column('review_tasks', 'finding_id', existing_type=sa.UUID(), nullable=False)
    op.drop_column('review_tasks', 'claim_id')
    op.drop_column('review_tasks', 'organization_id')

    op.drop_constraint('fk_findings_policy_rule', 'findings', type_='foreignkey')
    op.drop_constraint('fk_findings_claim', 'findings', type_='foreignkey')
    op.drop_constraint('fk_findings_organization', 'findings', type_='foreignkey')
    op.drop_index('idx_findings_policy_rule_id', table_name='findings')
    op.drop_index('idx_findings_org_id', table_name='findings')
    op.drop_index('idx_findings_claim_id', table_name='findings')
    op.drop_column('findings', 'policy_rule_id')
    op.drop_column('findings', 'claim_id')
    op.drop_column('findings', 'organization_id')

    op.drop_constraint('fk_analysis_runs_claim', 'analysis_runs', type_='foreignkey')
    op.drop_constraint('fk_analysis_runs_organization', 'analysis_runs', type_='foreignkey')
    op.drop_index('idx_analysis_runs_org_id', table_name='analysis_runs')
    op.drop_index('idx_analysis_runs_claim_id', table_name='analysis_runs')
    op.alter_column('analysis_runs', 'document_id', existing_type=sa.UUID(), nullable=False)
    op.drop_column('analysis_runs', 'claim_id')
    op.drop_column('analysis_runs', 'organization_id')

    op.drop_constraint('fk_documents_organization', 'documents', type_='foreignkey')
    op.drop_index('idx_documents_type', table_name='documents')
    op.drop_index('idx_documents_org_id', table_name='documents')
    op.drop_column('documents', 'document_type')
    op.drop_column('documents', 'organization_id')

    # Drop new tables in reverse dependency order
    op.drop_index('idx_claim_docs_doc_id', table_name='claim_documents')
    op.drop_index('idx_claim_docs_claim_id', table_name='claim_documents')
    op.drop_table('claim_documents')

    op.drop_index('idx_claim_items_claim_id', table_name='claim_line_items')
    op.drop_index('idx_claim_items_cat', table_name='claim_line_items')
    op.drop_table('claim_line_items')

    op.drop_index('idx_claims_org_status', table_name='claims')
    op.drop_index('idx_claims_number', table_name='claims')
    op.drop_index('idx_claims_employee', table_name='claims')
    op.drop_table('claims')

    op.drop_index('idx_policy_rules_version', table_name='policy_rules')
    op.drop_index('idx_policy_rules_status', table_name='policy_rules')
    op.drop_table('policy_rules')

    op.drop_index('idx_policy_versions_status', table_name='policy_versions')
    op.drop_index('idx_policy_versions_dates', table_name='policy_versions')
    op.drop_table('policy_versions')

    op.drop_index('idx_policies_status', table_name='policies')
    op.drop_index('idx_policies_org_cat', table_name='policies')
    op.drop_table('policies')

    op.drop_index('idx_org_members_role', table_name='organization_members')
    op.drop_index('idx_org_members_org_user', table_name='organization_members')
    op.drop_table('organization_members')

    op.drop_index('idx_departments_org_id', table_name='departments')
    op.drop_table('departments')

    op.drop_index('idx_organizations_status', table_name='organizations')
    op.drop_index('idx_organizations_slug', table_name='organizations')
    op.drop_table('organizations')
