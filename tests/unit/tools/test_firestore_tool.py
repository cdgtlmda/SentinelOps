"""
Comprehensive tests for tools.firestore_tool module.

Tests all Firestore tool functionality using REAL Google Cloud Firestore services.
100% production code, NO MOCKS - tests actual Firestore operations and ADK integration.
"""

import pytest
import uuid
import time
from datetime import datetime
from typing import Any, Dict, List

from google.cloud import firestore
from pydantic import ValidationError

from src.tools.firestore_tool import (
    FirestoreConfig,
    DocumentInput,
    QueryInput,
    BatchWriteInput,
    FirestoreTool,
)


class TestFirestoreConfig:
    """Test FirestoreConfig model and validation."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = FirestoreConfig(project_id="test-project")

        assert config.project_id == "test-project"
        assert config.database_id == "(default)"
        assert config.timeout == 30.0

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = FirestoreConfig(
            project_id="custom-project",
            database_id="custom-db",
            timeout=60.0
        )

        assert config.project_id == "custom-project"
        assert config.database_id == "custom-db"
        assert config.timeout == 60.0

    def test_timeout_validation_positive(self) -> None:
        """Test timeout validation accepts positive values."""
        config = FirestoreConfig(project_id="test", timeout=1.5)
        assert config.timeout == 1.5

    def test_timeout_validation_zero_fails(self) -> None:
        """Test timeout validation rejects zero."""
        with pytest.raises(ValidationError) as exc_info:
            FirestoreConfig(project_id="test", timeout=0.0)

        assert "Timeout must be positive" in str(exc_info.value)

    def test_timeout_validation_negative_fails(self) -> None:
        """Test timeout validation rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            FirestoreConfig(project_id="test", timeout=-5.0)

        assert "Timeout must be positive" in str(exc_info.value)


class TestDocumentInput:
    """Test DocumentInput model and validation."""

    def test_basic_document_input(self) -> None:
        """Test basic document input creation."""
        doc_input = DocumentInput(
            collection="test_collection",
            data={"name": "test", "value": 42}
        )

        assert doc_input.collection == "test_collection"
        assert doc_input.document_id is None
        assert doc_input.data == {"name": "test", "value": 42}
        assert doc_input.merge is False

    def test_document_input_with_id(self) -> None:
        """Test document input with explicit ID."""
        doc_input = DocumentInput(
            collection="test_collection",
            document_id="test_doc_123",
            data={"status": "active"},
            merge=True
        )

        assert doc_input.collection == "test_collection"
        assert doc_input.document_id == "test_doc_123"
        assert doc_input.data == {"status": "active"}
        assert doc_input.merge is True

    def test_document_input_empty_data(self) -> None:
        """Test document input with empty data."""
        doc_input = DocumentInput(collection="test", data={})
        assert doc_input.data == {}

    def test_document_input_complex_data(self) -> None:
        """Test document input with complex nested data."""
        complex_data = {
            "user": {
                "name": "John Doe",
                "preferences": ["email", "sms"],
                "metadata": {
                    "created": "2025-01-01",
                    "tags": ["admin", "power_user"]
                }
            },
            "counters": [1, 2, 3, 4, 5],
            "active": True
        }

        doc_input = DocumentInput(collection="users", data=complex_data)
        assert doc_input.data == complex_data


class TestQueryInput:
    """Test QueryInput model and validation."""

    def test_basic_query_input(self) -> None:
        """Test basic query input creation."""
        query_input = QueryInput(collection="test_collection")

        assert query_input.collection == "test_collection"
        assert query_input.filters is None
        assert query_input.order_by is None
        assert query_input.limit is None
        assert query_input.offset is None

    def test_query_input_with_filters(self) -> None:
        """Test query input with filters."""
        filters: List[Dict[str, Any]] = [
            {"field": "status", "op": "==", "value": "active"},
            {"field": "count", "op": ">=", "value": 10}
        ]

        query_input = QueryInput(collection="test", filters=filters)
        assert query_input.filters == filters

    def test_query_input_with_ordering(self) -> None:
        """Test query input with ordering."""
        order_by = [
            {"field": "created_at", "direction": "DESCENDING"},
            {"field": "name", "direction": "ASCENDING"}
        ]

        query_input = QueryInput(collection="test", order_by=order_by)
        assert query_input.order_by == order_by

    def test_query_input_with_pagination(self) -> None:
        """Test query input with pagination."""
        query_input = QueryInput(
            collection="test",
            limit=25,
            offset=50
        )

        assert query_input.limit == 25
        assert query_input.offset == 50

    def test_query_input_complete(self) -> None:
        """Test query input with all parameters."""
        query_input = QueryInput(
            collection="events",
            filters=[{"field": "type", "op": "==", "value": "security"}],
            order_by=[{"field": "timestamp", "direction": "DESCENDING"}],
            limit=100,
            offset=0
        )

        assert query_input.collection == "events"
        assert query_input.filters is not None
        assert len(query_input.filters) == 1
        assert query_input.order_by is not None
        assert len(query_input.order_by) == 1
        assert query_input.limit == 100
        assert query_input.offset == 0


class TestBatchWriteInput:
    """Test BatchWriteInput model and validation."""

    def test_basic_batch_input(self) -> None:
        """Test basic batch write input creation."""
        operations = [
            {
                "type": "set",
                "collection": "test",
                "document_id": "doc1",
                "data": {"name": "test1"}
            }
        ]

        batch_input = BatchWriteInput(operations=operations)
        assert batch_input.operations == operations

    def test_batch_input_multiple_operations(self) -> None:
        """Test batch input with multiple operation types."""
        operations: List[Dict[str, Any]] = [
            {
                "type": "set",
                "collection": "users",
                "document_id": "user1",
                "data": {"name": "Alice", "status": "active"}
            },
            {
                "type": "update",
                "collection": "users",
                "document_id": "user2",
                "data": {"last_login": "2025-06-13"}
            },
            {
                "type": "delete",
                "collection": "users",
                "document_id": "user3"
            }
        ]

        batch_input = BatchWriteInput(operations=operations)
        assert len(batch_input.operations) == 3
        assert batch_input.operations[0]["type"] == "set"
        assert batch_input.operations[1]["type"] == "update"
        assert batch_input.operations[2]["type"] == "delete"

    def test_batch_input_empty_operations(self) -> None:
        """Test batch input with empty operations list."""
        batch_input = BatchWriteInput(operations=[])
        assert batch_input.operations == []


class TestFirestoreTool:
    """Test FirestoreTool class and all operations using real Firestore."""

    @pytest.fixture
    def config(self) -> FirestoreConfig:
        """Create test configuration."""
        return FirestoreConfig(
            project_id="your-gcp-project-id",
            database_id="(default)",
            timeout=30.0
        )

    @pytest.fixture
    def firestore_tool(self, config: FirestoreConfig) -> FirestoreTool:
        """Create FirestoreTool instance."""
        return FirestoreTool(config)

    @pytest.fixture
    def test_collection(self) -> str:
        """Generate unique test collection name."""
        return f"test_firestore_tool_{uuid.uuid4().hex[:8]}"

    def test_tool_initialization(self, config: FirestoreConfig) -> None:
        """Test FirestoreTool initialization."""
        tool = FirestoreTool(config)

        assert tool.name == "firestore_tool"
        assert "Interact with Google Cloud Firestore" in tool.description
        assert tool.config == config
        assert tool._client is None

    def test_client_property_lazy_loading(self, firestore_tool: FirestoreTool) -> None:
        """Test client property creates client on first access."""
        assert firestore_tool._client is None

        client = firestore_tool.client
        assert isinstance(client, firestore.Client)
        assert firestore_tool._client is not None

        # Second access returns same client
        assert firestore_tool.client is client  # type: ignore[unreachable]

    def test_client_configuration(self, firestore_tool: FirestoreTool) -> None:
        """Test client is configured with correct project and database."""
        client = firestore_tool.client

        assert client.project == "your-gcp-project-id"
        # Note: database property not directly accessible in client
        # but connection should work with real Firestore

    def test_execute_unknown_operation(self, firestore_tool: FirestoreTool) -> None:
        """Test execute with unknown operation raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            firestore_tool.execute("unknown_operation")

        assert "Unknown operation: unknown_operation" in str(exc_info.value)

    def test_create_document_with_id(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test creating document with specified ID."""
        doc_id = f"test_doc_{uuid.uuid4().hex[:8]}"
        test_data = {
            "name": "Test Document",
            "description": "Created by test",
            "value": 42
        }

        result = firestore_tool.execute(
            "create",
            collection=test_collection,
            document_id=doc_id,
            data=test_data
        )

        assert result["success"] is True
        assert result["document_id"] == doc_id
        assert result["collection"] == test_collection
        assert "path" in result

        # Verify document was actually created
        verify_result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)
        assert verify_result["success"] is True
        assert verify_result["exists"] is True
        assert verify_result["data"]["name"] == "Test Document"
        assert verify_result["data"]["value"] == 42
        assert "created_at" in verify_result["data"]
        assert "updated_at" in verify_result["data"]

        # Cleanup
        firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_create_document_auto_id(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test creating document with auto-generated ID."""
        test_data = {
            "type": "auto_generated",
            "timestamp": datetime.utcnow().isoformat()
        }

        result = firestore_tool.execute(
            "create",
            collection=test_collection,
            data=test_data
        )

        assert result["success"] is True
        assert "document_id" in result
        assert len(result["document_id"]) > 0  # Auto-generated ID
        assert result["collection"] == test_collection

        # Verify document exists
        doc_id = result["document_id"]
        verify_result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)
        assert verify_result["success"] is True
        assert verify_result["exists"] is True
        assert verify_result["data"]["type"] == "auto_generated"

        # Cleanup
        firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_get_existing_document(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test getting an existing document."""
        # Create test document first
        doc_id = f"get_test_{uuid.uuid4().hex[:8]}"
        test_data = {"field1": "value1", "field2": 123}

        create_result = firestore_tool.execute(
            "create",
            collection=test_collection,
            document_id=doc_id,
            data=test_data
        )
        assert create_result["success"] is True

        # Test getting the document
        result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)

        assert result["success"] is True
        assert result["exists"] is True
        assert result["document_id"] == doc_id
        assert result["data"]["field1"] == "value1"
        assert result["data"]["field2"] == 123
        assert "create_time" in result
        assert "update_time" in result

        # Cleanup
        firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_get_nonexistent_document(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test getting a non-existent document."""
        doc_id = f"nonexistent_{uuid.uuid4().hex[:8]}"

        result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)

        assert result["success"] is True
        assert result["exists"] is False
        assert result["document_id"] == doc_id
        assert "Document not found" in result["message"]

    def test_update_document_merge_false(
        self, firestore_tool: FirestoreTool, test_collection: str
    ) -> None:
        """Test updating document without merge."""
        # Create test document
        doc_id = f"update_test_{uuid.uuid4().hex[:8]}"
        initial_data = {"field1": "initial", "field2": "keep_me"}

        firestore_tool.execute(
            "create", collection=test_collection, document_id=doc_id, data=initial_data
        )

        # Update without merge (should replace specified fields)
        update_data = {"field1": "updated", "field3": "new_field"}
        result = firestore_tool.execute(
            "update",
            collection=test_collection,
            document_id=doc_id,
            data=update_data,
            merge=False
        )

        assert result["success"] is True
        assert result["document_id"] == doc_id
        assert result["collection"] == test_collection
        assert result["merged"] is False

        # Verify update
        verify_result = firestore_tool.execute(
            "get", collection=test_collection, document_id=doc_id
        )
        assert verify_result["data"]["field1"] == "updated"
        assert verify_result["data"]["field2"] == "keep_me"  # Should still exist
        assert verify_result["data"]["field3"] == "new_field"
        assert "updated_at" in verify_result["data"]

        # Cleanup
        firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_update_document_merge_true(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test updating document with merge."""
        # Create test document
        doc_id = f"merge_test_{uuid.uuid4().hex[:8]}"
        initial_data = {"field1": "initial", "field2": "keep_me"}

        firestore_tool.execute("create", collection=test_collection, document_id=doc_id, data=initial_data)

        # Update with merge
        update_data = {"field1": "merged", "field3": "added"}
        result = firestore_tool.execute(
            "update",
            collection=test_collection,
            document_id=doc_id,
            data=update_data,
            merge=True
        )

        assert result["success"] is True
        assert result["merged"] is True

        # Verify merge
        verify_result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)
        assert verify_result["data"]["field1"] == "merged"
        assert verify_result["data"]["field2"] == "keep_me"
        assert verify_result["data"]["field3"] == "added"

        # Cleanup
        firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_delete_document(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test deleting a document."""
        # Create test document
        doc_id = f"delete_test_{uuid.uuid4().hex[:8]}"
        test_data = {"to_be_deleted": True}

        firestore_tool.execute("create", collection=test_collection, document_id=doc_id, data=test_data)

        # Verify document exists
        verify_result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)
        assert verify_result["exists"] is True

        # Delete document
        result = firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

        assert result["success"] is True
        assert result["document_id"] == doc_id
        assert result["collection"] == test_collection
        assert result["deleted"] is True

        # Verify document is gone
        verify_result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)
        assert verify_result["exists"] is False

    def test_query_collection_no_filters(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test querying collection without filters."""
        # Create test documents
        doc_ids = []
        for i in range(3):
            doc_id = f"query_test_{i}_{uuid.uuid4().hex[:8]}"
            test_data = {"index": i, "type": "query_test"}
            firestore_tool.execute("create", collection=test_collection, document_id=doc_id, data=test_data)
            doc_ids.append(doc_id)

        # Query collection
        result = firestore_tool.execute("query", collection=test_collection)

        assert result["success"] is True
        assert result["collection"] == test_collection
        assert result["count"] >= 3  # At least our test documents
        assert isinstance(result["documents"], list)

        # Verify document structure
        if result["documents"]:
            doc = result["documents"][0]
            assert "document_id" in doc
            assert "data" in doc
            assert "create_time" in doc
            assert "update_time" in doc

        # Cleanup
        for doc_id in doc_ids:
            firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_query_collection_with_filters(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test querying collection with filters."""
        # Create test documents with different statuses
        doc_ids = []
        statuses = ["active", "inactive", "active", "pending"]

        for i, status in enumerate(statuses):
            doc_id = f"filter_test_{i}_{uuid.uuid4().hex[:8]}"
            test_data = {"status": status, "priority": i}
            firestore_tool.execute("create", collection=test_collection, document_id=doc_id, data=test_data)
            doc_ids.append(doc_id)

        # Wait a bit for consistency
        time.sleep(1)

        # Query with filter
        filters = [{"field": "status", "op": "==", "value": "active"}]
        result = firestore_tool.execute("query", collection=test_collection, filters=filters)

        assert result["success"] is True
        assert result["count"] >= 2  # Should find at least 2 active documents

        # Verify all returned documents have status "active"
        for doc in result["documents"]:
            if "status" in doc["data"]:  # Our test documents
                assert doc["data"]["status"] == "active"

        # Cleanup
        for doc_id in doc_ids:
            firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_query_collection_with_ordering(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test querying collection with ordering."""
        # Create test documents with different priorities
        doc_ids = []
        priorities = [3, 1, 4, 2]

        for i, priority in enumerate(priorities):
            doc_id = f"order_test_{i}_{uuid.uuid4().hex[:8]}"
            test_data = {"priority": priority, "name": f"doc_{priority}"}
            firestore_tool.execute("create", collection=test_collection, document_id=doc_id, data=test_data)
            doc_ids.append(doc_id)

        # Wait for consistency
        time.sleep(1)

        # Query with ordering (descending by priority)
        order_by = [{"field": "priority", "direction": "DESCENDING"}]
        result = firestore_tool.execute("query", collection=test_collection, order_by=order_by)

        assert result["success"] is True

        # Check ordering in results (considering we might have other documents)
        test_docs = [doc for doc in result["documents"] if "priority" in doc["data"]]
        if len(test_docs) >= 2:
            # Verify descending order
            for i in range(len(test_docs) - 1):
                curr_priority = test_docs[i]["data"]["priority"]
                next_priority = test_docs[i + 1]["data"]["priority"]
                assert curr_priority >= next_priority

        # Cleanup
        for doc_id in doc_ids:
            firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_query_collection_with_limit_offset(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test querying collection with limit and offset."""
        # Create several test documents
        doc_ids = []
        for i in range(5):
            doc_id = f"pagination_test_{i}_{uuid.uuid4().hex[:8]}"
            test_data = {"index": i, "name": f"doc_{i}"}
            firestore_tool.execute("create", collection=test_collection, document_id=doc_id, data=test_data)
            doc_ids.append(doc_id)

        # Wait for consistency
        time.sleep(1)

        # Test limit
        result = firestore_tool.execute("query", collection=test_collection, limit=2)
        assert result["success"] is True
        assert result["count"] <= 2

        # Test offset (skip first 2)
        result = firestore_tool.execute("query", collection=test_collection, offset=2, limit=3)
        assert result["success"] is True
        assert result["count"] <= 3

        # Cleanup
        for doc_id in doc_ids:
            firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_batch_write_operations(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test batch write with multiple operation types."""
        doc_ids = [f"batch_test_{i}_{uuid.uuid4().hex[:8]}" for i in range(3)]

        # Create one document first for update test
        firestore_tool.execute("create", collection=test_collection, document_id=doc_ids[1], data={"status": "old"})

        # Prepare batch operations
        operations = [
            {
                "type": "set",
                "collection": test_collection,
                "document_id": doc_ids[0],
                "data": {"name": "batch_set", "value": 100}
            },
            {
                "type": "update",
                "collection": test_collection,
                "document_id": doc_ids[1],
                "data": {"status": "updated", "batch": True}
            },
            {
                "type": "set",
                "collection": test_collection,
                "document_id": doc_ids[2],
                "data": {"name": "batch_set_2", "value": 200}
            }
        ]

        # Execute batch
        result = firestore_tool.execute("batch_write", operations=operations)

        assert result["success"] is True
        assert result["operations"]["set"] == 2
        assert result["operations"]["update"] == 1
        assert result["operations"]["delete"] == 0
        assert result["total"] == 3

        # Verify documents were created/updated
        verify_result = firestore_tool.execute("get", collection=test_collection, document_id=doc_ids[0])
        assert verify_result["exists"] is True
        assert verify_result["data"]["name"] == "batch_set"

        verify_result = firestore_tool.execute("get", collection=test_collection, document_id=doc_ids[1])
        assert verify_result["exists"] is True
        assert verify_result["data"]["status"] == "updated"
        assert verify_result["data"]["batch"] is True

        # Cleanup
        for doc_id in doc_ids:
            firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)

    def test_batch_write_with_delete(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test batch write with delete operations."""
        # Create documents first
        doc_ids = [f"batch_delete_{i}_{uuid.uuid4().hex[:8]}" for i in range(2)]

        for doc_id in doc_ids:
            firestore_tool.execute("create", collection=test_collection, document_id=doc_id, data={"to_delete": True})

        # Batch delete
        operations = [
            {
                "type": "delete",
                "collection": test_collection,
                "document_id": doc_ids[0]
            },
            {
                "type": "delete",
                "collection": test_collection,
                "document_id": doc_ids[1]
            }
        ]

        result = firestore_tool.execute("batch_write", operations=operations)

        assert result["success"] is True
        assert result["operations"]["delete"] == 2
        assert result["total"] == 2

        # Verify documents were deleted
        for doc_id in doc_ids:
            verify_result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)
            assert verify_result["exists"] is False

    def test_batch_write_incomplete_operations(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test batch write skips incomplete operations."""
        operations = [
            {
                "type": "set",
                "collection": test_collection,
                "document_id": "valid_doc",
                "data": {"valid": True}
            },
            {
                "type": "set",
                # Missing collection
                "document_id": "invalid_doc",
                "data": {"invalid": True}
            },
            {
                "type": "set",
                "collection": test_collection,
                # Missing document_id
                "data": {"also_invalid": True}
            }
        ]

        result = firestore_tool.execute("batch_write", operations=operations)

        assert result["success"] is True
        assert result["total"] == 1  # Only valid operation processed

        # Cleanup valid document
        firestore_tool.execute("delete", collection=test_collection, document_id="valid_doc")

    def test_list_collections(self, firestore_tool: FirestoreTool) -> None:
        """Test listing collections."""
        result = firestore_tool.execute("list_collections")

        assert result["success"] is True
        assert "collections" in result
        assert "count" in result
        assert isinstance(result["collections"], list)
        assert result["count"] >= 0

        # If collections exist, verify structure
        if result["collections"]:
            collection = result["collections"][0]
            assert "id" in collection

    def test_create_index_placeholder(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test index creation placeholder functionality."""
        fields = [
            {"field": "status", "direction": "ASCENDING"},
            {"field": "priority", "direction": "DESCENDING"}
        ]

        result = firestore_tool.execute("create_index", collection=test_collection, fields=fields)

        assert result["success"] is True
        assert "Index creation logged" in result["message"]
        assert result["collection"] == test_collection
        assert result["fields"] == fields

    def test_get_schema(self, firestore_tool: FirestoreTool) -> None:
        """Test getting tool schema for ADK."""
        schema = firestore_tool.get_schema()

        assert schema["name"] == "firestore_tool"
        assert "description" in schema
        assert "operations" in schema

        # Verify operations structure
        operations = schema["operations"]
        assert "create" in operations
        assert "query" in operations
        assert "batch_write" in operations

        # Verify operation structure
        create_op = operations["create"]
        assert "description" in create_op
        assert "input" in create_op
        assert "output" in create_op

        # Verify input/output schemas have required fields
        assert "type" in create_op["input"]
        assert "properties" in create_op["output"]

    def test_error_handling_invalid_operation_args(self, firestore_tool: FirestoreTool) -> None:
        """Test error handling with invalid operation arguments."""
        # Try to create document without required collection
        result = firestore_tool.execute("create", data={"test": True})

        assert result["success"] is False
        assert "error" in result
        assert result["operation"] == "create"

    def test_timestamps_added_automatically(self, firestore_tool: FirestoreTool, test_collection: str) -> None:
        """Test that timestamps are added automatically to documents."""
        doc_id = f"timestamp_test_{uuid.uuid4().hex[:8]}"
        test_data = {"name": "timestamp_test"}

        # Create document
        firestore_tool.execute("create", collection=test_collection, document_id=doc_id, data=test_data)

        # Verify timestamps were added
        result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)
        assert result["exists"] is True
        assert "created_at" in result["data"]
        assert "updated_at" in result["data"]
        assert isinstance(result["data"]["created_at"], datetime)
        assert isinstance(result["data"]["updated_at"], datetime)

        # Update document and verify updated_at changes
        original_updated = result["data"]["updated_at"]
        time.sleep(1)  # Ensure timestamp difference

        firestore_tool.execute("update", collection=test_collection, document_id=doc_id, data={"updated": True})

        updated_result = firestore_tool.execute("get", collection=test_collection, document_id=doc_id)
        new_updated = updated_result["data"]["updated_at"]
        assert new_updated > original_updated

        # Cleanup
        firestore_tool.execute("delete", collection=test_collection, document_id=doc_id)


class TestFirestoreToolIntegration:
    """Integration tests combining multiple operations."""

    @pytest.fixture
    def firestore_tool(self) -> FirestoreTool:
        """Create FirestoreTool instance for integration tests."""
        config = FirestoreConfig(project_id="your-gcp-project-id")
        return FirestoreTool(config)

    @pytest.fixture
    def integration_collection(self) -> str:
        """Generate unique collection name for integration tests."""
        return f"integration_test_{uuid.uuid4().hex[:8]}"

    def test_complete_document_lifecycle(self, firestore_tool: FirestoreTool, integration_collection: str) -> None:
        """Test complete document lifecycle: create, read, update, delete."""
        doc_id = f"lifecycle_test_{uuid.uuid4().hex[:8]}"

        # Step 1: Create
        initial_data = {"name": "Lifecycle Test", "stage": "created", "version": 1}
        create_result = firestore_tool.execute("create",
                                               collection=integration_collection,
                                               document_id=doc_id,
                                               data=initial_data)
        assert create_result["success"] is True

        # Step 2: Read
        read_result = firestore_tool.execute("get", collection=integration_collection, document_id=doc_id)
        assert read_result["success"] is True
        assert read_result["exists"] is True
        assert read_result["data"]["stage"] == "created"

        # Step 3: Update
        update_data = {"stage": "updated", "version": 2}
        update_result = firestore_tool.execute("update",
                                               collection=integration_collection,
                                               document_id=doc_id,
                                               data=update_data)
        assert update_result["success"] is True

        # Verify update
        verify_result = firestore_tool.execute("get", collection=integration_collection, document_id=doc_id)
        assert verify_result["data"]["stage"] == "updated"
        assert verify_result["data"]["version"] == 2
        assert verify_result["data"]["name"] == "Lifecycle Test"  # Should still exist

        # Step 4: Delete
        delete_result = firestore_tool.execute("delete", collection=integration_collection, document_id=doc_id)
        assert delete_result["success"] is True

        # Verify deletion
        final_result = firestore_tool.execute("get", collection=integration_collection, document_id=doc_id)
        assert final_result["exists"] is False

    def test_query_with_complex_filters_and_operations(self, firestore_tool: FirestoreTool, integration_collection: str) -> None:
        """Test complex scenario with multiple documents and queries."""
        # Create test dataset
        test_docs = [
            {"name": "Doc A", "category": "urgent", "priority": 1, "active": True},
            {"name": "Doc B", "category": "normal", "priority": 2, "active": True},
            {"name": "Doc C", "category": "urgent", "priority": 3, "active": False},
            {"name": "Doc D", "category": "low", "priority": 4, "active": True},
        ]

        doc_ids = []
        for i, doc_data in enumerate(test_docs):
            doc_id = f"complex_test_{i}_{uuid.uuid4().hex[:8]}"
            firestore_tool.execute("create", collection=integration_collection, document_id=doc_id, data=doc_data)
            doc_ids.append(doc_id)

        # Wait for consistency
        time.sleep(1)

        # Test 1: Filter by category and active status
        filters = [
            {"field": "category", "op": "==", "value": "urgent"},
            {"field": "active", "op": "==", "value": True}
        ]
        result = firestore_tool.execute("query", collection=integration_collection, filters=filters)

        urgent_active_docs = [doc for doc in result["documents"]
                              if doc["data"].get("category") == "urgent" and doc["data"].get("active") is True]
        assert len(urgent_active_docs) == 1
        assert urgent_active_docs[0]["data"]["name"] == "Doc A"

        # Test 2: Order by priority with limit
        order_by = [{"field": "priority", "direction": "ASCENDING"}]
        result = firestore_tool.execute("query",
                                        collection=integration_collection,
                                        order_by=order_by,
                                        limit=2)

        # Should get first 2 documents in priority order
        priority_docs = [doc for doc in result["documents"] if "priority" in doc["data"]]
        if len(priority_docs) >= 2:
            assert priority_docs[0]["data"]["priority"] <= priority_docs[1]["data"]["priority"]

        # Cleanup
        for doc_id in doc_ids:
            firestore_tool.execute("delete", collection=integration_collection, document_id=doc_id)


if __name__ == "__main__":
    pytest.main([__file__])
