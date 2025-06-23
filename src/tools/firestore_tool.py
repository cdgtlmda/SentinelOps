"""Google Cloud Firestore tool for ADK agents.

This module provides a Firestore tool implementation using ADK's BaseTool
for performing database operations in Google Cloud Firestore.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from google.cloud import firestore
from pydantic import BaseModel, Field, field_validator

from src.common.adk_import_fix import BaseTool

logger = logging.getLogger(__name__)


class FirestoreConfig(BaseModel):
    """Configuration for Firestore operations."""

    project_id: str = Field(description="Google Cloud Project ID")
    database_id: str = Field(default="(default)", description="Firestore database ID")
    timeout: float = Field(default=30.0, description="Operation timeout in seconds")

    @field_validator("timeout")
    def validate_timeout(cls, v: float) -> float:  # pylint: disable=no-self-argument
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v


class DocumentInput(BaseModel):
    """Input schema for document operations."""

    collection: str = Field(description="Collection name")
    document_id: Optional[str] = Field(
        default=None, description="Document ID (auto-generated if not provided)"
    )
    data: Dict[str, Any] = Field(description="Document data")
    merge: bool = Field(default=False, description="Merge with existing document")


class QueryInput(BaseModel):
    """Input schema for query operations."""

    collection: str = Field(description="Collection name")
    filters: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Query filters: [{'field': 'name', 'op': '==', 'value': 'test'}]",
    )
    order_by: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Order by fields: [{'field': 'name', 'direction': 'ASCENDING'}]",
    )
    limit: Optional[int] = Field(
        default=None, description="Maximum documents to return"
    )
    offset: Optional[int] = Field(
        default=None, description="Number of documents to skip"
    )


class BatchWriteInput(BaseModel):
    """Input schema for batch write operations."""

    operations: List[Dict[str, Any]] = Field(
        description=(
            "List of operations: [{'type': 'set/update/delete', "
            "'collection': 'x', 'document_id': 'y', 'data': {...}}]"
        )
    )


class FirestoreTool(BaseTool):
    """ADK tool for interacting with Google Cloud Firestore.

    This tool provides methods for:
    - Creating, reading, updating, and deleting documents
    - Querying collections with filters and ordering
    - Batch operations for multiple documents
    - Transaction support
    """

    def __init__(self, config: FirestoreConfig):
        """Initialize the Firestore tool.

        Args:
            config: Firestore configuration
        """
        super().__init__(
            name="firestore_tool",
            description="Interact with Google Cloud Firestore for document database operations",
        )
        self.config = config
        self._client = None

    @property
    def client(self) -> firestore.Client:
        """Get or create the Firestore client."""
        if self._client is None:
            self._client = firestore.Client(
                project=self.config.project_id, database=self.config.database_id
            )
        return self._client

    def execute(self, operation: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a Firestore operation.

        Args:
            operation: The operation to perform
            **kwargs: Operation-specific arguments

        Returns:
            Operation result
        """
        operations: Dict[str, Callable[..., Dict[str, Any]]] = {
            "create": self._create_document,
            "get": self._get_document,
            "update": self._update_document,
            "delete": self._delete_document,
            "query": self._query_collection,
            "batch_write": self._batch_write,
            "list_collections": self._list_collections,
            "create_index": self._create_index,
        }

        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")

        try:
            func = operations[operation]
            return func(**kwargs)
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Firestore operation '%s' failed: %s", operation, str(e))
            return {"success": False, "error": str(e), "operation": operation}

    def _create_document(
        self,
        collection: str,
        document_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new document.

        Args:
            collection: Collection name
            document_id: Document ID (auto-generated if not provided)
            data: Document data

        Returns:
            Result dictionary with document reference
        """
        collection_ref = self.client.collection(collection)

        # Add timestamp
        data = data or {}
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()

        if document_id:
            doc_ref = collection_ref.document(document_id)
            doc_ref.set(data)
        else:
            _, doc_ref = collection_ref.add(data)

        logger.info("Created document %s in collection %s", doc_ref.id, collection)
        return {
            "success": True,
            "document_id": doc_ref.id,
            "collection": collection,
            "path": doc_ref.path,
        }

    def _get_document(self, collection: str, document_id: str) -> Dict[str, Any]:
        """Get a document by ID.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            Result dictionary with document data
        """
        doc_ref = self.client.collection(collection).document(document_id)
        doc = doc_ref.get()

        if doc.exists:
            return {
                "success": True,
                "exists": True,
                "document_id": document_id,
                "data": doc.to_dict(),
                "create_time": doc.create_time.isoformat() if doc.create_time else None,
                "update_time": doc.update_time.isoformat() if doc.update_time else None,
            }
        else:
            return {
                "success": True,
                "exists": False,
                "document_id": document_id,
                "message": "Document not found",
            }

    def _update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = False,
    ) -> Dict[str, Any]:
        """Update an existing document.

        Args:
            collection: Collection name
            document_id: Document ID
            data: Update data
            merge: Whether to merge with existing data

        Returns:
            Result dictionary
        """
        doc_ref = self.client.collection(collection).document(document_id)

        # Add updated timestamp
        data["updated_at"] = datetime.utcnow()

        if merge:
            doc_ref.set(data, merge=True)
        else:
            doc_ref.update(data)

        logger.info("Updated document %s in collection %s", document_id, collection)
        return {
            "success": True,
            "document_id": document_id,
            "collection": collection,
            "merged": merge,
        }

    def _delete_document(self, collection: str, document_id: str) -> Dict[str, Any]:
        """Delete a document.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            Result dictionary
        """
        doc_ref = self.client.collection(collection).document(document_id)
        doc_ref.delete()

        logger.info("Deleted document %s from collection %s", document_id, collection)
        return {
            "success": True,
            "document_id": document_id,
            "collection": collection,
            "deleted": True,
        }

    def _query_collection(
        self,
        collection: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        order_by: Optional[List[Dict[str, Any]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Query a collection with filters and ordering.

        Args:
            collection: Collection name
            filters: List of filter dictionaries
            order_by: List of order by dictionaries
            limit: Maximum documents to return
            offset: Number of documents to skip

        Returns:
            Result dictionary with matching documents
        """
        query = self.client.collection(collection)

        # Apply filters
        if filters:
            for filter_spec in filters:
                field = filter_spec.get("field")
                op = filter_spec.get("op", "==")
                value = filter_spec.get("value")

                if field and value is not None:
                    query = query.where(field, op, value)

        # Apply ordering
        if order_by:
            for order_spec in order_by:
                field = order_spec.get("field")
                direction = order_spec.get("direction", "ASCENDING")

                if field:
                    direction_constant = (
                        firestore.Query.DESCENDING
                        if direction.upper() == "DESCENDING"
                        else firestore.Query.ASCENDING
                    )
                    query = query.order_by(field, direction=direction_constant)

        # Apply offset
        if offset:
            query = query.offset(offset)

        # Apply limit
        if limit:
            query = query.limit(limit)

        # Execute query
        docs = query.stream()

        results = []
        for doc in docs:
            results.append(
                {
                    "document_id": doc.id,
                    "data": doc.to_dict(),
                    "create_time": (
                        doc.create_time.isoformat() if doc.create_time else None
                    ),
                    "update_time": (
                        doc.update_time.isoformat() if doc.update_time else None
                    ),
                }
            )

        return {
            "success": True,
            "collection": collection,
            "documents": results,
            "count": len(results),
        }

    def _batch_write(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform batch write operations.

        Args:
            operations: List of operation dictionaries

        Returns:
            Result dictionary
        """
        batch = self.client.batch()
        operation_count = {"set": 0, "update": 0, "delete": 0}

        for op in operations:
            op_type = op.get("type")
            collection = op.get("collection")
            document_id = op.get("document_id")
            data = op.get("data", {})

            if not collection or not document_id:
                continue

            doc_ref = self.client.collection(collection).document(document_id)

            if op_type == "set":
                data["updated_at"] = datetime.utcnow()
                if "created_at" not in data:
                    data["created_at"] = datetime.utcnow()
                batch.set(doc_ref, data)
                operation_count["set"] += 1

            elif op_type == "update":
                data["updated_at"] = datetime.utcnow()
                batch.update(doc_ref, data)
                operation_count["update"] += 1

            elif op_type == "delete":
                batch.delete(doc_ref)
                operation_count["delete"] += 1

        # Commit the batch
        batch.commit()

        total_operations = sum(operation_count.values())
        logger.info("Completed batch write with %d operations", total_operations)

        return {
            "success": True,
            "operations": operation_count,
            "total": total_operations,
        }

    def _list_collections(self) -> Dict[str, Any]:
        """List all collections in the database.

        Returns:
            Result dictionary with collection list
        """
        collections = []

        for collection in self.client.collections():
            collections.append({"id": collection.id})

        return {"success": True, "collections": collections, "count": len(collections)}

    def _create_index(
        self, collection: str, fields: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Create an index (placeholder - actual index creation requires admin SDK).

        Args:
            collection: Collection name
            fields: List of field specifications

        Returns:
            Result dictionary
        """
        # Note: Creating indexes programmatically requires the Admin SDK
        # This is a placeholder that logs the request
        logger.info(
            "Index creation requested for collection '%s' with fields: %s. Please create manually in GCP Console.",
            collection,
            fields,
        )

        return {
            "success": True,
            "message": "Index creation logged. Please create manually in GCP Console.",
            "collection": collection,
            "fields": fields,
        }

    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input/output schema for ADK.

        Returns:
            Schema dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "operations": {
                "create": {
                    "description": "Create a new document",
                    "input": DocumentInput.model_json_schema(),
                    "output": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "document_id": {"type": "string"},
                            "collection": {"type": "string"},
                            "path": {"type": "string"},
                        },
                    },
                },
                "query": {
                    "description": "Query documents in a collection",
                    "input": QueryInput.model_json_schema(),
                    "output": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "documents": {"type": "array"},
                            "count": {"type": "integer"},
                        },
                    },
                },
                "batch_write": {
                    "description": "Perform batch write operations",
                    "input": BatchWriteInput.model_json_schema(),
                    "output": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "operations": {"type": "object"},
                            "total": {"type": "integer"},
                        },
                    },
                },
            },
        }
