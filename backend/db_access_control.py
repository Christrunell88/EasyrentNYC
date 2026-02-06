"""
Database Access Control Layer for NoFeesApts.com
=================================================
Enforces strict write permissions for production collections.

HARD RULE:
No automated process may write directly into units or buildings (production)
collections except:
1. Manual admin approval (via promotion service)
2. Internal leasing system feeds (with valid API key)

Crawler roles are RESTRICTED to staging collections only.
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timezone
from functools import wraps
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class WriteSource(Enum):
    """Authorized sources for production writes."""
    ADMIN_APPROVAL = "admin_approval"
    LEASING_SYSTEM = "leasing_system"
    SYSTEM_MIGRATION = "system_migration"  # One-time migrations only
    

class UnauthorizedWriteError(Exception):
    """Raised when an unauthorized write to production is attempted."""
    pass


class DatabaseAccessControl:
    """
    Controls and audits all database write operations.
    
    Production collections (units, buildings) are protected.
    Only authorized sources can write to them.
    """
    
    # Protected production collections
    PROTECTED_COLLECTIONS = {'units', 'buildings'}
    
    # Staging collections (crawlers can write here)
    STAGING_COLLECTIONS = {'units_staging', 'buildings_staging'}
    
    # History/audit collections (system can write)
    AUDIT_COLLECTIONS = {'price_changes', 'status_changes', 'write_audit_log'}
    
    def __init__(self, db):
        self.db = db
        self._write_hooks: List[Callable] = []
    
    def add_write_hook(self, hook: Callable):
        """Add a hook to be called on every production write."""
        self._write_hooks.append(hook)
    
    async def _log_write_attempt(
        self,
        collection: str,
        operation: str,
        source: str,
        authorized: bool,
        user_id: Optional[str] = None,
        document_id: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """Log all write attempts for audit trail."""
        log_entry = {
            "id": str(uuid.uuid4()),
            "collection": collection,
            "operation": operation,
            "source": source,
            "authorized": authorized,
            "user_id": user_id,
            "document_id": document_id,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ip_address": None  # Can be added from request context
        }
        
        try:
            await self.db.write_audit_log.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to log write attempt: {e}")
        
        if not authorized:
            logger.warning(
                f"UNAUTHORIZED WRITE BLOCKED: {operation} on {collection} "
                f"from source '{source}'"
            )
        else:
            logger.info(
                f"Authorized write: {operation} on {collection} "
                f"from source '{source}' by user {user_id}"
            )
    
    def is_production_collection(self, collection: str) -> bool:
        """Check if a collection is a protected production collection."""
        return collection in self.PROTECTED_COLLECTIONS
    
    def is_staging_collection(self, collection: str) -> bool:
        """Check if a collection is a staging collection."""
        return collection in self.STAGING_COLLECTIONS
    
    async def authorized_production_write(
        self,
        collection: str,
        operation: str,
        source: WriteSource,
        user_id: str,
        document: Dict,
        api_key: Optional[str] = None
    ) -> Dict:
        """
        Perform an authorized write to a production collection.
        
        Args:
            collection: Target collection name
            operation: 'insert', 'update', or 'delete'
            source: The authorized WriteSource
            user_id: ID of the user/system performing the write
            document: The document to write
            api_key: Required for LEASING_SYSTEM source
            
        Returns:
            Result of the write operation
            
        Raises:
            UnauthorizedWriteError: If the write is not authorized
        """
        # Validate source
        if source == WriteSource.LEASING_SYSTEM:
            if not api_key or not await self._validate_leasing_api_key(api_key):
                await self._log_write_attempt(
                    collection, operation, source.value, 
                    authorized=False, user_id=user_id,
                    details={"reason": "Invalid or missing API key"}
                )
                raise UnauthorizedWriteError(
                    "Invalid API key for leasing system feed"
                )
        
        if source == WriteSource.ADMIN_APPROVAL:
            if not user_id:
                await self._log_write_attempt(
                    collection, operation, source.value,
                    authorized=False,
                    details={"reason": "Missing user_id for admin approval"}
                )
                raise UnauthorizedWriteError(
                    "Admin approval requires user_id"
                )
        
        # Perform the write
        result = None
        document_id = document.get('id')
        
        try:
            if operation == 'insert':
                await self.db[collection].insert_one(document)
                result = {"inserted_id": document_id}
            elif operation == 'update':
                query = {"id": document_id}
                update_result = await self.db[collection].update_one(
                    query, {"$set": document}
                )
                result = {
                    "matched": update_result.matched_count,
                    "modified": update_result.modified_count
                }
            elif operation == 'delete':
                delete_result = await self.db[collection].delete_one(
                    {"id": document_id}
                )
                result = {"deleted": delete_result.deleted_count}
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            # Log successful write
            await self._log_write_attempt(
                collection, operation, source.value,
                authorized=True, user_id=user_id,
                document_id=document_id,
                details={"result": result}
            )
            
            # Call write hooks
            for hook in self._write_hooks:
                try:
                    await hook(collection, operation, source, document)
                except Exception as e:
                    logger.error(f"Write hook error: {e}")
            
            return result
            
        except Exception as e:
            await self._log_write_attempt(
                collection, operation, source.value,
                authorized=True, user_id=user_id,
                document_id=document_id,
                details={"error": str(e)}
            )
            raise
    
    async def _validate_leasing_api_key(self, api_key: str) -> bool:
        """Validate a leasing system API key."""
        # Check against stored API keys
        key_record = await self.db.api_keys.find_one({
            "key": api_key,
            "type": "leasing_system",
            "is_active": True
        })
        return key_record is not None
    
    async def staging_write(
        self,
        collection: str,
        operation: str,
        document: Dict,
        crawler_source: str
    ) -> Dict:
        """
        Perform a write to a staging collection.
        
        Crawlers should use this method for all writes.
        
        Args:
            collection: Must be a staging collection
            operation: 'insert', 'update', or 'delete'
            document: The document to write
            crawler_source: Identifier for the crawler
            
        Returns:
            Result of the write operation
            
        Raises:
            UnauthorizedWriteError: If trying to write to non-staging collection
        """
        # HARD RULE: Only allow writes to staging collections
        if not self.is_staging_collection(collection):
            await self._log_write_attempt(
                collection, operation, f"crawler:{crawler_source}",
                authorized=False,
                details={"reason": "Crawler attempted write to non-staging collection"}
            )
            raise UnauthorizedWriteError(
                f"Crawlers can only write to staging collections. "
                f"Attempted write to '{collection}' is BLOCKED."
            )
        
        # Perform staging write
        document_id = document.get('id')
        result = None
        
        try:
            if operation == 'insert':
                await self.db[collection].insert_one(document)
                result = {"inserted_id": document_id}
            elif operation == 'update':
                update_result = await self.db[collection].update_one(
                    {"id": document_id}, {"$set": document}
                )
                result = {
                    "matched": update_result.matched_count,
                    "modified": update_result.modified_count
                }
            elif operation == 'delete':
                delete_result = await self.db[collection].delete_one(
                    {"id": document_id}
                )
                result = {"deleted": delete_result.deleted_count}
            
            # Log staging write (for audit)
            await self._log_write_attempt(
                collection, operation, f"crawler:{crawler_source}",
                authorized=True,
                document_id=document_id,
                details={"result": result}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Staging write error: {e}")
            raise


# Decorator for protecting production writes
def require_authorized_source(allowed_sources: List[WriteSource]):
    """
    Decorator to enforce authorized source for production writes.
    
    Usage:
        @require_authorized_source([WriteSource.ADMIN_APPROVAL])
        async def my_function(source: WriteSource, user_id: str, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            source = kwargs.get('source')
            if source not in allowed_sources:
                raise UnauthorizedWriteError(
                    f"Function {func.__name__} requires source to be one of "
                    f"{[s.value for s in allowed_sources]}, got {source}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global access control instance
_access_control: Optional[DatabaseAccessControl] = None


def get_access_control(db) -> DatabaseAccessControl:
    """Get or create the database access control instance."""
    global _access_control
    if _access_control is None:
        _access_control = DatabaseAccessControl(db)
    return _access_control


def init_access_control(db) -> DatabaseAccessControl:
    """Initialize the database access control (call at app startup)."""
    global _access_control
    _access_control = DatabaseAccessControl(db)
    logger.info("Database access control initialized")
    return _access_control
