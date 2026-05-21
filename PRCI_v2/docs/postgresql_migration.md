# PostgreSQL Migration Guide for PRCI v2

## Overview

This guide provides a comprehensive migration path from SQLite to PostgreSQL for the PRCI v2 application. PostgreSQL offers superior performance, scalability, and feature support for production deployments.

## Migration Benefits

### Performance Improvements
- **Concurrent Connections**: True multi-user support
- **Query Optimization**: Advanced query planner and optimizer
- **Indexing**: More sophisticated indexing options (GIN, GiST, partial indexes)
- **Connection Pooling**: Efficient connection management
- **Caching**: Advanced caching mechanisms

### Feature Enhancements
- **JSONB**: Native JSON support with indexing
- **Full-Text Search**: Built-in full-text search capabilities
- **Window Functions**: Advanced analytical queries
- **Partitioning**: Table partitioning for large datasets
- **Replication**: Built-in replication support

### Operational Benefits
- **Backup & Recovery**: Advanced backup tools
- **Monitoring**: Comprehensive monitoring and logging
- **Security**: Row-level security, encryption
- **Scalability**: Read replicas, sharding support

## Prerequisites

### System Requirements
- PostgreSQL 12+ (recommended 14+)
- Python 3.8+
- Psycopg2 or asyncpg driver
- Sufficient disk space for data migration

### Software Dependencies
```bash
# PostgreSQL client libraries
pip install psycopg2-binary

# Alternative async driver
pip install asyncpg

# SQLAlchemy with PostgreSQL support
pip install sqlalchemy psycopg2
```

## Migration Strategy

### Phase 1: Preparation

#### 1.1 Environment Setup
```bash
# Create PostgreSQL database
createdb prci_v2

# Create user (optional)
createuser prci_user
```

#### 1.2 Backup Current Data
```bash
# Backup SQLite database
sqlite3 prci_v2.db ".backup prci_backup.db"

# Export data for verification
sqlite3 prci_v2.db ".dump --data-only" > prci_data.sql
```

#### 1.3 Update Configuration
```bash
# Set PostgreSQL environment variables
export POSTGRESQL_URL="postgresql://prci_user:password@localhost:5432/prci_v2"
export DB_POOL_SIZE=10
export DB_MAX_OVERFLOW=20
```

### Phase 2: Schema Migration

#### 2.1 Initialize PostgreSQL Schema
```python
# Using Alembic with PostgreSQL
alembic upgrade head

# Or manually create schema
python -c "
from db.config import DatabaseConfig
from db.connection import initialize_database

config = DatabaseConfig.from_env()
config.postgresql_url = 'postgresql://prci_user:password@localhost:5432/prci_v2'
initialize_database(config)
"
```

#### 2.2 Verify Schema
```sql
-- Connect to PostgreSQL and verify tables
\dt
\d users
\d conversations
\d messages
\d assessments
\d scores
\d interventions
\d user_interventions
\d reports
```

### Phase 3: Data Migration

#### 3.1 Export from SQLite
```python
# Export script: export_sqlite_data.py
import sqlite3
import json
import csv
from datetime import datetime

def export_table_to_csv(table_name, output_file):
    conn = sqlite3.connect('prci_v2.db')
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM {table_name} WHERE is_deleted = 'N'")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(columns)
        writer.writerows(rows)
    
    conn.close()

# Export all tables
tables = ['users', 'user_sessions', 'conversations', 'messages', 
          'assessments', 'scores', 'interventions', 'user_interventions', 'reports']

for table in tables:
    export_table_to_csv(table, f'{table}_export.csv')
```

#### 3.2 Import to PostgreSQL
```python
# Import script: import_postgresql_data.py
import psycopg2
import csv
from datetime import datetime

def import_csv_to_postgresql(table_name, csv_file, conn):
    cursor = conn.cursor()
    
    with open(csv_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Handle data type conversions
            processed_row = {}
            for key, value in row.items():
                if value == '':
                    processed_row[key] = None
                elif key in ['created_at', 'updated_at', 'deleted_at', 'last_login_at', 
                          'email_verified_at', 'recommended_at', 'accepted_at', 'started_at', 
                          'completed_at', 'last_message_at', 'expires_at', 'last_activity_at',
                          'email_sent_at', 'last_accessed_at', 'date_range_start', 'date_range_end']:
                    processed_row[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if value else None
                elif key in ['is_deleted', 'is_verified', 'is_active', 'is_edited', 
                          'share_data', 'email_notifications', 'evidence_based', 'is_public', 
                          'email_sent']:
                    processed_row[key] = value == 'True'
                elif key in ['id', 'user_id', 'conversation_id', 'assessment_id', 
                          'intervention_id', 'message_count', 'token_count', 'processing_time_ms',
                          'generation_time_ms', 'file_size_bytes', 'download_count',
                          'duration_minutes', 'difficulty_level', 'priority', 'effectiveness_score',
                          'completion_rate', 'progress_percentage', 'user_rating', 'effectiveness_rating',
                          'feedback_rating']:
                    processed_row[key] = int(value) if value else None
                elif key in ['value', 'confidence', 'completion_rate']:
                    processed_row[key] = float(value) if value else None
                else:
                    processed_row[key] = value
            
            # Build INSERT query
            columns = list(processed_row.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            cursor.execute(insert_query, list(processed_row.values()))
    
    conn.commit()

# Connect to PostgreSQL
conn = psycopg2.connect("postgresql://prci_user:password@localhost:5432/prci_v2")

# Import all tables
for table in tables:
    import_csv_to_postgresql(table, f'{table}_export.csv', conn)

conn.close()
```

#### 3.3 Data Validation
```sql
-- Verify data counts
SELECT 
    'users' as table_name, COUNT(*) as count
FROM users WHERE is_deleted = 'N'
UNION ALL
SELECT 
    'conversations' as table_name, COUNT(*) as count
FROM conversations WHERE is_deleted = 'N'
UNION ALL
SELECT 
    'assessments' as table_name, COUNT(*) as count
FROM assessments WHERE is_deleted = 'N';

-- Verify relationships
SELECT u.id as user_id, COUNT(c.id) as conversation_count
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id AND c.is_deleted = 'N'
WHERE u.is_deleted = 'N'
GROUP BY u.id;
```

### Phase 4: Application Configuration

#### 4.1 Update Database Configuration
```python
# Update db/config.py
from config import DatabaseConfig

class ProductionDatabaseConfig(DatabaseConfig):
    postgresql_url = "postgresql://prci_user:password@localhost:5432/prci_v2"
    
    # PostgreSQL-specific settings
    pool_size = 20
    max_overflow = 30
    pool_timeout = 30
    pool_recycle = 3600
    
    # Connection settings
    connect_timeout = 10
    statement_timeout = 30000
    
    # Performance settings
    echo = False  # Disable in production
```

#### 4.2 Environment Variables
```bash
# Production environment
export DATABASE_URL="postgresql://prci_user:password@localhost:5432/prci_v2"
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=30
export DB_POOL_TIMEOUT=30
export DB_POOL_RECYCLE=3600

# Disable SQL logging in production
export DB_ECHO=false
```

#### 4.3 Update Alembic Configuration
```ini
# migrations/alembic.ini
sqlalchemy.url = postgresql://prci_user:password@localhost:5432/prci_v2

# PostgreSQL-specific settings
[alembic]
# ... existing settings ...
```

## Performance Optimization

### 1. Indexing Strategy
```sql
-- Create optimized indexes for PostgreSQL
CREATE INDEX CONCURRENTLY idx_users_email_active ON users(email) WHERE is_deleted = 'N';
CREATE INDEX CONCURRENTLY idx_conversations_user_active ON conversations(user_id) WHERE is_deleted = 'N';
CREATE INDEX CONCURRENTLY idx_assessments_user_completed ON assessments(user_id, completed_at DESC) WHERE is_deleted = 'N';

-- JSONB indexes for JSON fields
CREATE INDEX CONCURRENTLY idx_interventions_target_root_causes ON interventions USING GIN(target_root_causes);
CREATE INDEX CONCURRENTLY idx_assessments_root_cause_data ON assessments USING GIN(root_cause_data);
```

### 2. Connection Pooling
```python
# Optimize connection pool for PostgreSQL
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    postgresql_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)
```

### 3. Query Optimization
```sql
-- Use PostgreSQL-specific features
-- Window functions for analytics
SELECT user_id, 
       COUNT(*) OVER (PARTITION BY user_id) as total_conversations,
       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as recent_rank
FROM conversations 
WHERE is_deleted = 'N'
QUALIFY recent_rank <= 5;

-- CTEs for complex queries
WITH user_stats AS (
    SELECT user_id, 
           COUNT(*) as conversation_count,
           MAX(created_at) as last_conversation
    FROM conversations 
    WHERE is_deleted = 'N'
    GROUP BY user_id
)
SELECT u.*, us.conversation_count, us.last_conversation
FROM users u
JOIN user_stats us ON u.id = us.user_id;
```

## Monitoring and Maintenance

### 1. Monitoring Setup
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;  # Log queries > 1s

-- Create monitoring views
CREATE VIEW performance_stats AS
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_read,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables;
```

### 2. Backup Strategy
```bash
# Automated backups
pg_dump -h localhost -U prci_user -d prci_v2 > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backups
pg_dump -h localhost -U prci_user -d prci_v2 | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Incremental backups using WAL archiving
archive_command = 'cp %p /backup/archive/%f'
```

### 3. Maintenance Tasks
```sql
-- Update table statistics
ANALYZE;

-- Rebuild indexes
REINDEX DATABASE prci_v2;

-- Vacuum old tables
VACUUM FULL ANALYZE;
```

## Rollback Plan

### 1. Immediate Rollback
```bash
# Switch back to SQLite
export DATABASE_URL="sqlite:///./prci_v2.db"

# Restart application
```

### 2. Data Recovery
```bash
# Restore from backup
psql -h localhost -U prci_user -d prci_v2 < backup_before_migration.sql

# Or restore SQLite if needed
cp prci_backup.db prci_v2.db
```

## Testing Strategy

### 1. Unit Testing
```python
# Test database connections
def test_postgresql_connection():
    engine = create_engine(postgresql_url)
    with engine.connect() as conn:
        result = conn.execute("SELECT 1").fetchone()
        assert result[0] == 1

# Test data integrity
def test_user_relationships():
    # Verify foreign key constraints
    # Test cascade deletes
    # Validate data types
```

### 2. Integration Testing
```python
# Test full application workflow
def test_assessment_workflow():
    # Create user
    # Create session
    # Create assessment
    # Generate scores
    # Verify relationships
```

### 3. Performance Testing
```python
# Load testing
def test_concurrent_users():
    # Simulate multiple users
    # Measure response times
    # Monitor resource usage
```

## Security Considerations

### 1. Connection Security
```python
# Use SSL connections
postgresql_url = "postgresql://user:password@localhost:5432/prci_v2?sslmode=require"

# Connection encryption
engine = create_engine(
    postgresql_url,
    connect_args={
        "sslmode": "require",
        "sslcert": "/path/to/client-cert.pem",
        "sslkey": "/path/to/client-key.pem"
    }
)
```

### 2. Data Protection
```sql
-- Enable row-level security
CREATE POLICY user_data_policy ON users FOR ALL TO prci_user USING (id = current_user_id());

-- Enable encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

## Deployment Checklist

### Pre-Migration
- [ ] Backup current SQLite database
- [ ] Set up PostgreSQL server
- [ ] Create PostgreSQL database and user
- [ ] Test PostgreSQL connectivity
- [ ] Prepare migration scripts

### Migration
- [ ] Export data from SQLite
- [ ] Create PostgreSQL schema
- [ ] Import data to PostgreSQL
- [ ] Validate data integrity
- [ ] Update application configuration

### Post-Migration
- [ ] Test application functionality
- [ ] Verify performance improvements
- [ ] Set up monitoring
- [ ] Configure backup procedures
- [ ] Update documentation

## Troubleshooting

### Common Issues
1. **Connection Errors**: Check PostgreSQL service status and credentials
2. **Data Type Issues**: Verify data type conversions during import
3. **Performance Issues**: Check indexes and query plans
4. **Encoding Issues**: Ensure consistent UTF-8 encoding

### Debug Commands
```sql
-- Check PostgreSQL status
SELECT version();

-- Check active connections
SELECT * FROM pg_stat_activity;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public';
```

This migration guide provides a comprehensive path from SQLite to PostgreSQL while maintaining data integrity and optimizing for production performance.
