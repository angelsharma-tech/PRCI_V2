"""
Base Model for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin to add timestamp fields to models"""
    
    created_at = Column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality"""
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="Soft delete timestamp"
    )
    
    is_deleted = Column(
        String(1),
        default='N',
        nullable=False,
        comment="Soft delete flag (Y/N)"
    )


class AuditMixin:
    """Mixin to add audit fields"""
    
    created_by = Column(
        String(255),
        nullable=True,
        comment="User who created the record"
    )
    
    updated_by = Column(
        String(255),
        nullable=True,
        comment="User who last updated the record"
    )


class TableNameMixin:
    """Mixin to automatically generate table names"""
    
    @declared_attr
    def __tablename__(cls):
        # Convert CamelCase to snake_case and add plural
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        return f"{name}s"


class BaseModel(Base, TableNameMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Base model class with common fields"""
    
    __abstract__ = True
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Primary key"
    )
    
    def to_dict(self, exclude_fields=None):
        """Convert model instance to dictionary"""
        exclude_fields = exclude_fields or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: dict, exclude_fields=None):
        """Update model instance from dictionary"""
        exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
    
    def soft_delete(self):
        """Soft delete the record"""
        self.deleted_at = datetime.utcnow()
        self.is_deleted = 'Y'
    
    def restore(self):
        """Restore soft deleted record"""
        self.deleted_at = None
        self.is_deleted = 'N'
    
    @classmethod
    def get_table_name(cls):
        """Get the table name for this model"""
        return cls.__tablename__
