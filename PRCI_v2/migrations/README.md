# Database Migrations for PRCI v2

This directory contains Alembic database migrations for the PRCI v2 application.

## Structure

- `alembic.ini` - Alembic configuration file
- `env.py` - Alembic environment setup
- `script.py.mako` - Template for migration files
- `versions/` - Directory containing migration files (created by Alembic)

## Usage

### Environment Setup

Make sure you have the required environment variables set:

```bash
# For SQLite (default)
export DATABASE_URL="sqlite:///./prci_v2.db"

# For PostgreSQL
export POSTGRESQL_URL="postgresql://user:password@localhost:5432/prci_v2"
```

### Running Migrations

#### Create new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

#### Apply migrations:
```bash
alembic upgrade head
```

#### Rollback to specific revision:
```bash
alembic downgrade <revision_id>
```

#### Get current revision:
```bash
alembic current
```

#### Show migration history:
```bash
alembic history
```

## Migration Best Practices

1. **Always use `--autogenerate`** when creating migrations to ensure database schema matches models
2. **Review generated migrations** before applying to ensure they're correct
3. **Test migrations** on a development database before applying to production
4. **Keep migration descriptions descriptive** for future reference
5. **Never modify existing migration files** - create new ones instead

## Database Support

### SQLite (Default)
- Used for development and small deployments
- File-based storage
- Supports most features but has some limitations

### PostgreSQL (Production)
- Recommended for production deployments
- Full feature support
- Better performance and concurrency
- Supports advanced features like proper indexing, constraints

## Migration Path from SQLite to PostgreSQL

1. **Export data from SQLite**
2. **Set up PostgreSQL database**
3. **Apply migrations to PostgreSQL**
4. **Import data to PostgreSQL**
5. **Update environment variables**
6. **Test thoroughly**

## Environment Variables

| Variable | Description | Default |
|-----------|-------------|----------|
| `DATABASE_URL` | Primary database URL | `sqlite:///./prci_v2.db` |
| `POSTGRESQL_URL` | PostgreSQL override URL | None |
| `DB_ECHO` | Enable SQL logging | `false` |
| `DB_POOL_SIZE` | Connection pool size | `5` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `10` |
| `DB_POOL_TIMEOUT` | Pool timeout (seconds) | `30` |
| `DB_POOL_RECYCLE` | Connection recycle time (seconds) | `3600` |
| `SQLITE_CHECK_SAME_THREAD` | SQLite thread checking | `false` |
| `SQLITE_TIMEOUT` | SQLite timeout (seconds) | `20` |

## Troubleshooting

### Migration Issues
- Check database connectivity
- Verify environment variables
- Ensure models are properly imported
- Review migration SQL for syntax errors

### Performance Issues
- Use appropriate connection pooling
- Monitor query performance
- Consider database-specific optimizations

### Data Integrity
- Always backup before major migrations
- Test migrations on staging first
- Verify data after migration

## Notes

- Migrations are designed to be reversible
- Always test rollback procedures
- Keep migration history for audit purposes
- Document any manual interventions required
