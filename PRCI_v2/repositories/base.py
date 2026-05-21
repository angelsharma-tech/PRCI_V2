"""
Base Repository for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, or_, desc, asc

from db.connection import get_session_manager
from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Generic type for model classes
ModelType = TypeVar('ModelType')


class BaseRepository(ABC, Generic[ModelType]):
    """
    Abstract base repository class with common CRUD operations
    """
    
    def __init__(self, session: Session = None, model_class: Type[ModelType] = None):
        self.session_manager = get_session_manager()
        self._session = session
        self.model_class = model_class or self.get_model_class()
    
    @property
    def session(self) -> Session:
        """Get database session"""
        if self._session is None:
            raise RuntimeError("Session not provided. Use with session context.")
        return self._session
    
    @abstractmethod
    def get_model_class(self) -> Type[ModelType]:
        """Return the model class for this repository"""
        pass
    
    # Basic CRUD operations
    
    def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create a new record
        
        Args:
            data: Dictionary with field values
            
        Returns:
            Created model instance
        """
        try:
            instance = self.model_class(**data)
            self.session.add(instance)
            self.session.commit()
            self.session.refresh(instance)
            logger.info(f"Created {self.model_class.__name__}: {instance.id}")
            return instance
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Integrity error creating {self.model_class.__name__}: {e}")
            raise ValueError(f"Record already exists or violates constraints: {str(e)}")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error creating {self.model_class.__name__}: {e}")
            raise
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get record by ID
        
        Args:
            id: Record ID
            
        Returns:
            Model instance or None
        """
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.id == id,
                self.model_class.is_deleted == 'N'
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {self.model_class.__name__} by ID {id}: {e}")
            raise
    
    def get_all(self, include_deleted: bool = False) -> List[ModelType]:
        """
        Get all records
        
        Args:
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            List of model instances
        """
        try:
            query = self.session.query(self.model_class)
            if not include_deleted:
                query = query.filter(self.model_class.is_deleted == 'N')
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all {self.model_class.__name__}: {e}")
            raise
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update record by ID
        
        Args:
            id: Record ID
            data: Dictionary with field values to update
            
        Returns:
            Updated model instance or None
        """
        try:
            instance = self.get_by_id(id)
            if instance:
                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                self.session.commit()
                self.session.refresh(instance)
                logger.info(f"Updated {self.model_class.__name__}: {id}")
                return instance
            return None
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error updating {self.model_class.__name__} {id}: {e}")
            raise
    
    def delete(self, id: int, soft_delete: bool = True) -> bool:
        """
        Delete record by ID
        
        Args:
            id: Record ID
            soft_delete: Whether to soft delete (default) or hard delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            instance = self.get_by_id(id)
            if instance:
                if soft_delete and hasattr(instance, 'soft_delete'):
                    instance.soft_delete()
                else:
                    self.session.delete(instance)
                self.session.commit()
                logger.info(f"Deleted {self.model_class.__name__}: {id}")
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error deleting {self.model_class.__name__} {id}: {e}")
            raise
    
    def restore(self, id: int) -> bool:
        """
        Restore soft-deleted record
        
        Args:
            id: Record ID
            
        Returns:
            True if restored, False if not found
        """
        try:
            instance = self.session.query(self.model_class).filter(
                self.model_class.id == id,
                self.model_class.is_deleted == 'Y'
            ).first()
            
            if instance and hasattr(instance, 'restore'):
                instance.restore()
                self.session.commit()
                logger.info(f"Restored {self.model_class.__name__}: {id}")
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error restoring {self.model_class.__name__} {id}: {e}")
            raise
    
    # Query operations
    
    def find_by(self, **kwargs) -> List[ModelType]:
        """
        Find records by field values
        
        Args:
            **kwargs: Field name/value pairs
            
        Returns:
            List of matching model instances
        """
        try:
            query = self.session.query(self.model_class).filter(
                self.model_class.is_deleted == 'N'
            )
            
            for key, value in kwargs.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Database error finding {self.model_class.__name__} by {kwargs}: {e}")
            raise
    
    def find_one_by(self, **kwargs) -> Optional[ModelType]:
        """
        Find one record by field values
        
        Args:
            **kwargs: Field name/value pairs
            
        Returns:
            Matching model instance or None
        """
        try:
            query = self.session.query(self.model_class).filter(
                self.model_class.is_deleted == 'N'
            )
            
            for key, value in kwargs.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            return query.first()
        except SQLAlchemyError as e:
            logger.error(f"Database error finding {self.model_class.__name__} by {kwargs}: {e}")
            raise
    
    def search(self, search_term: str, search_fields: List[str]) -> List[ModelType]:
        """
        Search records by text in specified fields
        
        Args:
            search_term: Text to search for
            search_fields: List of field names to search in
            
        Returns:
            List of matching model instances
        """
        try:
            if not search_term or not search_fields:
                return []
            
            query = self.session.query(self.model_class).filter(
                self.model_class.is_deleted == 'N'
            )
            
            # Build OR conditions for search fields
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model_class, field):
                    field_attr = getattr(self.model_class, field)
                    search_conditions.append(field_attr.contains(search_term))
            
            if search_conditions:
                query = query.filter(or_(*search_conditions))
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Database error searching {self.model_class.__name__}: {e}")
            raise
    
    def count(self, include_deleted: bool = False) -> int:
        """
        Count all records
        
        Args:
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Number of records
        """
        try:
            query = self.session.query(self.model_class)
            if not include_deleted:
                query = query.filter(self.model_class.is_deleted == 'N')
            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Database error counting {self.model_class.__name__}: {e}")
            raise
    
    def exists(self, **kwargs) -> bool:
        """
        Check if record exists
        
        Args:
            **kwargs: Field name/value pairs
            
        Returns:
            True if record exists
        """
        try:
            query = self.session.query(self.model_class).filter(
                self.model_class.is_deleted == 'N'
            )
            
            for key, value in kwargs.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            return query.first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error checking {self.model_class.__name__} existence: {e}")
            raise
    
    # Advanced query operations
    
    def get_with_pagination(self, page: int = 1, per_page: int = 20, 
                         order_by: str = None, order_desc: bool = False) -> Dict[str, Any]:
        """
        Get records with pagination
        
        Args:
            page: Page number (1-based)
            per_page: Records per page
            order_by: Field name to order by
            order_desc: Whether to order descending
            
        Returns:
            Dictionary with records and pagination info
        """
        try:
            query = self.session.query(self.model_class).filter(
                self.model_class.is_deleted == 'N'
            )
            
            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                order_field = getattr(self.model_class, order_by)
                if order_desc:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
            
            # Calculate pagination
            total = query.count()
            offset = (page - 1) * per_page
            records = query.offset(offset).limit(per_page).all()
            
            return {
                'records': records,
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'has_next': offset + per_page < total,
                'has_prev': page > 1
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error paginating {self.model_class.__name__}: {e}")
            raise
    
    def get_recent(self, days: int = 30, limit: int = None) -> List[ModelType]:
        """
        Get recent records
        
        Args:
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of recent model instances
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = self.session.query(self.model_class).filter(
                and_(
                    self.model_class.is_deleted == 'N',
                    self.model_class.created_at >= cutoff_date
                )
            ).order_by(desc(self.model_class.created_at))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting recent {self.model_class.__name__}: {e}")
            raise
    
    # Bulk operations
    
    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records
        
        Args:
            data_list: List of dictionaries with field values
            
        Returns:
            List of created model instances
        """
        try:
            instances = [self.model_class(**data) for data in data_list]
            self.session.add_all(instances)
            self.session.commit()
            
            # Refresh all instances to get IDs
            for instance in instances:
                self.session.refresh(instance)
            
            logger.info(f"Bulk created {len(instances)} {self.model_class.__name__} records")
            return instances
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error bulk creating {self.model_class.__name__}: {e}")
            raise
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Update multiple records
        
        Args:
            updates: List of dictionaries with 'id' and field values
            
        Returns:
            True if successful
        """
        try:
            for update_data in updates:
                if 'id' in update_data:
                    id = update_data.pop('id')
                    self.session.query(self.model_class).filter(
                        self.model_class.id == id
                    ).update(update_data)
            
            self.session.commit()
            logger.info(f"Bulk updated {len(updates)} {self.model_class.__name__} records")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error bulk updating {self.model_class.__name__}: {e}")
            raise
