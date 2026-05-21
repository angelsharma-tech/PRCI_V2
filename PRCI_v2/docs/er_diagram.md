# PRCI v2 Entity Relationship Diagram

## ER Diagram Overview

The PRCI v2 database consists of 9 core entities with clear relationships designed to support mental health assessment, conversation tracking, intervention management, and reporting capabilities.

## Entity Relationship Summary

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Users      │    │  User Sessions   │    │  Conversations  │
│                 │    │                 │    │                 │
│ PK id          │    │ PK id           │    │ PK id           │
│ UN email       │    │ UN session_id    │    │ FK user_id      │
│ UN username    │    │ FK user_id      │    │                 │
│ status         │    │ expires_at       │    │ status          │
│ role           │    │ last_activity    │    │ message_count   │
│ ...           │    │ ...             │    │ last_message_at │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────────────────────────────────┐
                    │                                             │
         ┌─────────▼─────────┐    ┌─────────▼─────────┐    ┌─────────▼─────────┐
         │    Assessments    │    │   User Interventions │    │      Reports      │
         │                  │    │                     │    │                  │
         │ PK id           │    │ PK id              │    │ PK id           │
         │ FK user_id      │    │ FK user_id         │    │ FK user_id      │
         │ status          │    │ FK intervention_id │    │ report_type     │
         │ risk_level      │    │ FK assessment_id   │    │ format          │
         │ completed_at    │    │ status             │    │ status          │
         │ ...             │    │ progress           │    │ file_data       │
         └──────────────────┘    │ ...                │    │ ...             │
                                 │                     │    └──────────────────┘
                    ┌─────────▼─────────┐    │
                    │      Scores       │    │
                    │                  │    │
                    │ PK id           │    │
                    │ FK assessment_id │    │
                    │ score_type      │    │
                    │ value           │    │
                    │ confidence      │    │
                    │ ...             │    │
                    └──────────────────┘    │
                                 │
                    ┌─────────▼─────────┐    │
                    │   Interventions   │    │
                    │                  │    │
                    │ PK id           │    │
                    │ title           │    │
                    │ type            │    │
                    │ category        │    │
                    │ priority        │    │
                    │ effectiveness   │    │
                    │ ...             │    │
                    └──────────────────┘    │
                                 │
                    ┌─────────▼─────────┐    │
                    │     Messages     │    │
                    │                  │    │
                    │ PK id           │    │
                    │ FK conversation_id│    │
                    │ role            │    │
                    │ content         │    │
                    │ feedback_rating │    │
                    │ ...             │    │
                    └──────────────────┘    │
                                 └───────────────────────┘
```

## Detailed Relationships

### 1. Users (Central Entity)

**Primary Entity**: All user-related data flows from the Users table.

**Relationships**:
- `1:N` → User Sessions (Each user can have multiple sessions)
- `1:N` → Conversations (Each user can have multiple conversations)
- `1:N` → Assessments (Each user can have multiple assessments)
- `1:N` → User Interventions (Each user can have multiple interventions)
- `1:N` → Reports (Each user can have multiple reports)

**Key Fields**:
- `id` (Primary Key)
- `email` (Unique, Natural Key)
- `username` (Unique)
- `status`, `role` (User classification)
- `created_at`, `last_login_at` (Temporal data)

### 2. User Sessions

**Purpose**: Track user login sessions and activity state.

**Relationships**:
- `N:1` → Users (Many sessions belong to one user)

**Key Fields**:
- `id` (Primary Key)
- `session_id` (Unique session identifier)
- `user_id` (Foreign Key to Users)
- `expires_at`, `last_activity_at` (Session management)
- `streamlit_session_state` (Streamlit integration)

### 3. Conversations & Messages

**Purpose**: Chat conversation tracking with message history.

**Relationships**:
- `N:1` → Users (Many conversations per user)
- `1:N` → Messages (One conversation has many messages)
- `1:1` → Assessments (Optional current assessment reference)

**Key Fields**:
- **Conversations**: `id`, `user_id`, `status`, `message_count`, `last_message_at`
- **Messages**: `id`, `conversation_id`, `role`, `content`, `feedback_rating`

### 4. Assessments & Scores

**Purpose**: Mental health assessment results and detailed scoring.

**Relationships**:
- `N:1` → Users (Many assessments per user)
- `1:N` → Scores (One assessment has multiple scores)
- `1:N` → User Interventions (Assessments can recommend interventions)
- `1:1` → Conversations (Assessment can be current for conversation)

**Key Fields**:
- **Assessments**: `id`, `user_id`, `status`, `risk_level`, `completed_at`
- **Scores**: `id`, `assessment_id`, `score_type`, `value`, `confidence`

### 5. Interventions & User Interventions

**Purpose**: Intervention templates and user-specific tracking.

**Relationships**:
- `1:N` → User Interventions (One template can have many user instances)
- `N:1` → Users (Many user interventions per user)
- `N:1` → Assessments (User interventions can be linked to assessments)

**Key Fields**:
- **Interventions**: `id`, `title`, `type`, `category`, `priority`, `effectiveness_score`
- **User Interventions**: `id`, `user_id`, `intervention_id`, `status`, `progress`, `user_rating`

### 6. Reports

**Purpose**: Generated reports and analytics.

**Relationships**:
- `N:1` → Users (Many reports per user)

**Key Fields**:
- `id`, `user_id`, `report_type`, `format`, `status`, `file_data`, `access_token`

## Cardinality Summary

| Entity | Relationship | Cardinality |
|---------|-------------|-------------|
| Users → User Sessions | One-to-Many | 1:N |
| Users → Conversations | One-to-Many | 1:N |
| Users → Assessments | One-to-Many | 1:N |
| Users → User Interventions | One-to-Many | 1:N |
| Users → Reports | One-to-Many | 1:N |
| Conversations → Messages | One-to-Many | 1:N |
| Assessments → Scores | One-to-Many | 1:N |
| Interventions → User Interventions | One-to-Many | 1:N |
| Conversations → Assessments | One-to-One (Optional) | 1:1 |
| Assessments → User Interventions | One-to-Many | 1:N |

## Data Flow Patterns

### 1. User Journey Flow
```
User → Session → Conversation → Assessment → Intervention → Report
```

### 2. Assessment Flow
```
User Input → Assessment → Scores → Risk Analysis → Intervention Recommendation
```

### 3. Conversation Flow
```
User → Conversation → Messages → (Optional Assessment) → Response
```

### 4. Intervention Flow
```
Assessment Result → Intervention Recommendation → User Acceptance → Progress Tracking → Completion
```

### 5. Reporting Flow
```
User Data → Assessment History → Intervention History → Report Generation → Delivery
```

## Key Design Decisions

### 1. Soft Deletes
- All major entities use soft deletes (`is_deleted` flag)
- Preserves data integrity and audit trail
- Enables data recovery and analytics

### 2. Central User Entity
- Users table is the central hub
- All user-related data references Users
- Supports future authentication and authorization

### 3. Flexible Data Storage
- JSON fields for extensible data storage
- Accommodates future feature requirements
- Maintains schema stability

### 4. Temporal Tracking
- Comprehensive timestamp fields
- Supports analytics and reporting
- Enables trend analysis

### 5. Performance Optimization
- Strategic indexing on foreign keys and query fields
- Supports efficient joins and filtering
- Scales with data growth

## Future Extensibility

### 1. Multi-tenancy
- Schema supports tenant isolation
- User-based data separation
- Scalable architecture

### 2. Advanced Analytics
- Rich data for machine learning
- User behavior tracking
- Intervention effectiveness analysis

### 3. Integration Points
- External system integration ready
- API-friendly data structure
- Webhook support capabilities

This ER diagram provides a comprehensive foundation for the PRCI v2 mental health platform while maintaining flexibility for future growth and feature development.
