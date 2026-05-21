# PRCI v2 Database Schema Documentation

## Overview

The PRCI v2 database schema is designed to support persistent storage for mental health assessments, conversations, interventions, and reports. The schema follows best practices for data integrity, scalability, and maintainability.

## Database Architecture

### Design Principles

1. **Modularity**: Each entity has its own table with clear relationships
2. **Scalability**: Designed to handle growth in users and data
3. **Data Integrity**: Foreign key constraints and proper indexing
4. **Audit Trail**: Created/updated timestamps and soft deletes
5. **Multi-Database Support**: SQLite for development, PostgreSQL for production

### Core Entities

```
Users
├── User Sessions
├── Conversations
│   └── Messages
├── Assessments
│   └── Scores
├── User Interventions
│   └── Interventions
└── Reports
```

## Table Schema

### 1. Users (`users`)

**Purpose**: Store user account information and preferences

**Columns**:
- `id` (PK): Primary key
- `email` (UNIQUE): User email address
- `username` (UNIQUE): Optional username
- `first_name`: User's first name
- `last_name`: User's last name
- `full_name`: Display name
- `password_hash`: Hashed password (for future auth)
- `is_verified`: Email verification status
- `status`: Account status (ACTIVE/INACTIVE/SUSPENDED/PENDING)
- `role`: User role (USER/ADMIN/MODERATOR)
- `bio`: User biography
- `avatar_url`: Profile picture URL
- `timezone`: User timezone
- `language`: Preferred language
- `preferences`: JSON preferences
- `share_data`: Data sharing consent
- `email_notifications`: Email notification preferences
- `last_login_at`: Last login timestamp
- `email_verified_at`: Email verification timestamp
- **Audit Fields**: created_at, updated_at, deleted_at, is_deleted, created_by, updated_by

**Indexes**:
- Primary key on `id`
- Unique index on `email`
- Unique index on `username`
- Index on `is_deleted`

### 2. User Sessions (`user_sessions`)

**Purpose**: Track user login sessions and activity

**Columns**:
- `id` (PK): Primary key
- `session_id` (UNIQUE): Session identifier
- `user_id` (FK): Reference to users
- `user_agent`: Browser user agent
- `ip_address`: User IP address
- `is_active`: Session active status
- `session_data`: JSON session data
- `streamlit_session_state`: Streamlit state data
- `expires_at`: Session expiration
- `last_activity_at`: Last activity timestamp
- **Audit Fields**: created_at, updated_at, deleted_at, is_deleted, created_by, updated_by

**Indexes**:
- Primary key on `id`
- Unique index on `session_id`
- Index on `user_id`
- Index on `is_deleted`

### 3. Conversations (`conversations`)

**Purpose**: Store chat conversations between users and AI assistant

**Columns**:
- `id` (PK): Primary key
- `user_id` (FK): Reference to users
- `title`: Conversation title
- `status`: Conversation status (ACTIVE/ARCHIVED/DELETED)
- `context_data`: JSON conversation context
- `current_assessment_id` (FK): Current assessment reference
- `message_count`: Total message count
- `last_message_at`: Last message timestamp
- **Audit Fields**: created_at, updated_at, deleted_at, is_deleted, created_by, updated_by

**Indexes**:
- Primary key on `id`
- Index on `user_id`
- Index on `is_deleted`

### 4. Messages (`messages`)

**Purpose**: Store individual messages in conversations

**Columns**:
- `id` (PK): Primary key
- `conversation_id` (FK): Reference to conversations
- `role`: Message role (USER/ASSISTANT/SYSTEM)
- `content`: Message content
- `token_count`: Token count
- `processing_time_ms`: Processing time
- `model_used`: AI model used
- `is_edited`: Edit status
- `edited_at`: Edit timestamp
- `feedback_rating`: User feedback (1-5)
- `feedback_comment`: User feedback text
- **Audit Fields**: created_at, updated_at, deleted_at, is_deleted, created_by, updated_by

**Indexes**:
- Primary key on `id`
- Index on `conversation_id`
- Index on `is_deleted`

### 5. Assessments (`assessments`)

**Purpose**: Store mental health assessments and results

**Columns**:
- `id` (PK): Primary key
- `user_id` (FK): Reference to users
- `assessment_type`: Type (AUTOMATIC/MANUAL/SCHEDULED)
- `status`: Status (PENDING/IN_PROGRESS/COMPLETED/FAILED)
- `title`: Assessment title
- `description`: Assessment description
- `input_text`: User input text
- `input_data`: JSON input data
- `model_version`: AI model version
- `model_confidence`: Model confidence score
- `risk_level`: Overall risk level
- `primary_root_cause`: Main identified cause
- `root_cause_data`: JSON root cause analysis
- `processing_time_ms`: Processing time
- `completed_at`: Completion timestamp
- **Audit Fields**: created_at, updated_at, deleted_at, is_deleted, created_by, updated_by

**Indexes**:
- Primary key on `id`
- Index on `user_id`
- Index on `is_deleted`

### 6. Scores (`scores`)

**Purpose**: Store detailed assessment scores

**Columns**:
- `id` (PK): Primary key
- `assessment_id` (FK): Reference to assessments
- `score_type`: Score type (DEPRESSION/ANXIETY/STRESS/OVERALL)
- `value`: Score value (0.0-1.0)
- `confidence`: Confidence score
- `calculation_method`: Calculation method
- `additional_data`: JSON additional data
- **Audit Fields**: created_at, updated_at, deleted_at, is_deleted, created_by, updated_by

**Indexes**:
- Primary key on `id`
- Index on `assessment_id`
- Index on `is_deleted`

### 7. Interventions (`interventions`)

**Purpose**: Store intervention templates and strategies

**Columns**:
- `id` (PK): Primary key
- `title`: Intervention title
- `description`: Intervention description
- `intervention_type`: Type (MINDFULNESS/ACTIVITY/SOCIAL/PRODUCTIVITY/THERAPEUTIC/EDUCATIONAL)
- `category`: Category (COPING_STRATEGY/LIFESTYLE_CHANGE/SKILL_BUILDING/SUPPORT_RESOURCE)
- `target_root_causes`: JSON target root causes
- `target_risk_levels`: JSON target risk levels
- `target_score_ranges`: JSON target score ranges
- `duration_minutes`: Estimated duration
- `difficulty_level`: Difficulty (1-5)
- `priority`: Priority (1-5, 1=highest)
- `instructions`: Step-by-step instructions
- `resources`: JSON additional resources
- `effectiveness_score`: Average effectiveness (1-5)
- `completion_rate`: Historical completion rate
- `status`: Status (ACTIVE/INACTIVE/ARCHIVED)
- `version`: Intervention version
- `evidence_based`: Evidence-based flag
- **Audit Fields**: created_at, updated_at, deleted_at, is_deleted, created_by, updated_by

**Indexes**:
- Primary key on `id`
- Index on `is_deleted`

### 8. User Interventions (`user_interventions`)

**Purpose**: Track user-specific intervention assignments and progress

**Columns**:
- `id` (PK): Primary key
- `user_id` (FK): Reference to users
- `intervention_id` (FK): Reference to interventions
- `assessment_id` (FK): Context assessment
- `status`: Status (RECOMMENDED/ACCEPTED/IN_PROGRESS/COMPLETED/REJECTED/SKIPPED)
- `recommended_at`: Recommendation timestamp
- `accepted_at`: Acceptance timestamp
- `started_at`: Start timestamp
- `completed_at`: Completion timestamp
- `progress_percentage`: Progress (0.0-1.0)
- `user_rating`: User rating (1-5)
- `user_feedback`: User feedback text
- `effectiveness_rating`: Perceived effectiveness (1-5)
- `personalized_notes`: Personalized notes
- `modifications`: JSON user modifications
- **Audit Fields**: created_at, updated_at, deleted_at, is_deleted, created_by, updated_by

**Indexes**:
- Primary key on `id`
- Index on `user_id`
- Index on `intervention_id`
- Index on `is_deleted`

### 9. Reports (`reports`)

**Purpose**: Store generated reports and analytics

**Columns**:
- `id` (PK): Primary key
- `user_id` (FK): Reference to users
- `title`: Report title
- `report_type`: Type (COMPREHENSIVE/SUMMARY/TREND/INTERVENTION/CUSTOM)
- `format`: Format (PDF/HTML/JSON/CSV)
- `content`: Text content
- `file_data`: Binary file data
- `file_path`: File storage path
- `file_size_bytes`: File size
- `description`: Report description
- `parameters`: JSON generation parameters
- `assessment_ids`: JSON assessment references
- `date_range_start`: Data start date
- `date_range_end`: Data end date
- `status`: Status (PENDING/GENERATING/COMPLETED/FAILED/EXPIRED)
- `generation_time_ms`: Generation time
- `is_public`: Public access flag
- `access_token` (UNIQUE): Public access token
- `expires_at`: Expiration date
- `email_sent`: Email sent flag
- `email_sent_at`: Email sent timestamp
- `download_count`: Download counter
- `last_accessed_at`: Last access timestamp
- **Audit Fields**: created_at, updated_at, deleted_at, is_deleted, created_by, updated_by

**Indexes**:
- Primary key on `id`
- Index on `user_id`
- Index on `is_deleted`
- Unique index on `access_token`

## Relationships

### One-to-Many Relationships
- `users` → `user_sessions` (1:N)
- `users` → `conversations` (1:N)
- `users` → `assessments` (1:N)
- `users` → `user_interventions` (1:N)
- `users` → `reports` (1:N)
- `conversations` → `messages` (1:N)
- `assessments` → `scores` (1:N)
- `interventions` → `user_interventions` (1:N)

### Many-to-One Relationships
- `conversations` → `users` (N:1)
- `messages` → `conversations` (N:1)
- `assessments` → `users` (N:1)
- `scores` → `assessments` (N:1)
- `user_interventions` → `users` (N:1)
- `user_interventions` → `interventions` (N:1)
- `reports` → `users` (N:1)

### Optional Relationships
- `conversations.current_assessment_id` → `assessments` (1:1, optional)
- `user_interventions.assessment_id` → `assessments` (1:1, optional)

## Data Types and Constraints

### Enums
- **UserStatus**: ACTIVE, INACTIVE, SUSPENDED, PENDING
- **UserRole**: USER, ADMIN, MODERATOR
- **ConversationStatus**: ACTIVE, ARCHIVED, DELETED
- **MessageRole**: USER, ASSISTANT, SYSTEM
- **AssessmentType**: AUTOMATIC, MANUAL, SCHEDULED
- **AssessmentStatus**: PENDING, IN_PROGRESS, COMPLETED, FAILED
- **ScoreType**: DEPRESSION, ANXIETY, STRESS, OVERALL
- **InterventionType**: MINDFULNESS, ACTIVITY, SOCIAL, PRODUCTIVITY, THERAPEUTIC, EDUCATIONAL
- **InterventionCategory**: COPING_STRATEGY, LIFESTYLE_CHANGE, SKILL_BUILDING, SUPPORT_RESOURCE
- **InterventionStatus**: ACTIVE, INACTIVE, ARCHIVED
- **UserInterventionStatus**: RECOMMENDED, ACCEPTED, IN_PROGRESS, COMPLETED, REJECTED, SKIPPED
- **ReportType**: COMPREHENSIVE, SUMMARY, TREND, INTERVENTION, CUSTOM
- **ReportFormat**: PDF, HTML, JSON, CSV
- **ReportStatus**: PENDING, GENERATING, COMPLETED, FAILED, EXPIRED

### Constraints
- All foreign keys have proper constraints
- Unique constraints on email, username, session_id, access_token
- NOT NULL constraints on critical fields
- Check constraints for enum values

## Indexing Strategy

### Primary Indexes
- All tables have primary key indexes

### Foreign Key Indexes
- All foreign key columns are indexed for join performance

### Unique Indexes
- `users.email`, `users.username`
- `user_sessions.session_id`
- `reports.access_token`

### Performance Indexes
- `users.is_deleted`, `conversations.is_deleted`, etc. for soft delete queries
- Timestamp fields for date-based queries

## Data Integrity

### Soft Deletes
- All tables use soft deletes via `is_deleted` flag and `deleted_at` timestamp
- Prevents data loss and maintains audit trail

### Audit Trail
- `created_at`, `updated_at` timestamps on all records
- `created_by`, `updated_by` fields for change tracking

### Referential Integrity
- Foreign key constraints ensure data consistency
- Cascade delete for dependent records

## Performance Considerations

### Query Optimization
- Appropriate indexes for common query patterns
- Composite indexes for complex queries
- Partitioning considerations for large datasets

### Storage Optimization
- JSON fields for flexible data storage
- Binary storage for file data
- Text fields for long content

### Scalability
- Designed for horizontal scaling
- Connection pooling support
- Database-agnostic design

## Security Considerations

### Data Protection
- Password hashing (when implemented)
- Access tokens for report sharing
- Data sharing consent tracking

### Privacy
- Soft deletes preserve user data
- Personal data isolation by user
- Audit logging for compliance

## Migration Strategy

### Version Control
- Alembic migrations for schema changes
- Reversible migrations where possible
- Migration testing procedures

### Backward Compatibility
- Additive changes preferred
- Deprecation warnings for removed features
- Data migration scripts for major changes

## Database-Specific Considerations

### SQLite (Development)
- File-based storage
- Limited concurrent connections
- Suitable for development and small deployments

### PostgreSQL (Production)
- Client-server architecture
- Full concurrency support
- Advanced features (JSONB, indexes, etc.)
- Better performance and scalability

## Monitoring and Maintenance

### Health Checks
- Connection validation
- Table existence verification
- Performance metrics collection

### Cleanup Procedures
- Expired session cleanup
- Old report cleanup
- Log rotation and archiving

This schema provides a robust foundation for the PRCI v2 application's data persistence needs while maintaining flexibility for future enhancements.
