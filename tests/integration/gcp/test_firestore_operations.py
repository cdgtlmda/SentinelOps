"""Integration tests for Firestore operations."""

import uuid
from datetime import datetime
from typing import Any, Dict

import pytest
from google.cloud import firestore_v1 as firestore


class TestFirestoreOperations:
    """Test Firestore connectivity and operations."""

    @pytest.fixture(scope="class")
    def firestore_client(self) -> firestore.Client:
        """Create Firestore client."""
        return firestore.Client()

    @pytest.fixture(scope="class")
    def test_collection(self) -> str:
        """Name of test collection."""
        return "test_integration"

    @pytest.fixture
    def test_document_data(self) -> Dict[str, Any]:
        """Generate test document data."""
        return {
            "test_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow(),
            "test_type": "integration_test",
            "data": {"value": 42, "status": "active", "tags": ["test", "integration"]},
        }

    def test_firestore_connection(self, firestore_client: firestore.Client) -> None:
        """Test that Firestore client can connect."""
        assert firestore_client is not None
        # Try to list collections to verify connection
        try:
            collections = list(firestore_client.collections())
            assert isinstance(collections, list)
        except (ValueError, RuntimeError, TypeError) as e:
            pytest.fail(f"Failed to connect to Firestore: {str(e)}")

    def test_required_collections_exist(
        self, firestore_client: firestore.Client
    ) -> None:
        """Test that required collections exist."""
        required_collections = ["incidents", "audit_logs"]

        existing_collections = []
        for collection in firestore_client.collections():
            existing_collections.append(collection.id)

        for required in required_collections:
            assert (
                required in existing_collections
            ), f"Required collection {required} not found"

    def test_document_create(
        self,
        firestore_client: firestore.Client,
        test_collection: str,
        test_document_data: Dict[str, Any],
    ) -> None:
        """Test creating a document."""
        doc_id = test_document_data["test_id"]
        doc_ref = firestore_client.collection(test_collection).document(doc_id)

        try:
            # Create document
            doc_ref.set(test_document_data)

            # Verify it was created
            doc = doc_ref.get()
            assert doc.exists
            assert doc.id == doc_id

            # Clean up
            doc_ref.delete()

        except (PermissionError, ConnectionError, ValueError, RuntimeError) as e:
            pytest.skip(f"Firestore operation failed: {e}")
        finally:
            # Cleanup
            try:
                doc_ref.delete()
            except (PermissionError, ConnectionError, ValueError, RuntimeError):
                pass  # Cleanup failure is acceptable

    def test_document_update(
        self,
        firestore_client: firestore.Client,
        test_collection: str,
        test_document_data: Dict[str, Any],
    ) -> None:
        """Test updating a document."""
        doc_id = test_document_data["test_id"]
        doc_ref = firestore_client.collection(test_collection).document(doc_id)

        try:
            # Create document
            doc_ref.set(test_document_data)

            # Update document
            update_data = {
                "updated_at": datetime.utcnow(),
                "data.status": "updated",
                "data.new_field": "test_value",
            }
            doc_ref.update(update_data)

            # Verify update
            doc = doc_ref.get()
            doc_data = doc.to_dict()
            assert doc_data is not None
            assert doc_data["data"]["status"] == "updated"
            assert doc_data["data"]["new_field"] == "test_value"
            assert "updated_at" in doc_data

            # Clean up
            doc_ref.delete()

        except (PermissionError, ConnectionError, ValueError, RuntimeError) as e:
            pytest.skip(f"Firestore operation failed: {e}")
        finally:
            # Cleanup
            try:
                doc_ref.delete()
            except (PermissionError, ConnectionError, ValueError, RuntimeError):
                pass  # Cleanup failure is acceptable

    def test_query_operations(
        self, firestore_client: firestore.Client, test_collection: str
    ) -> None:
        """Test query operations."""
        # Create multiple test documents
        test_docs = []
        for i in range(5):
            doc_data = {
                "test_id": f"query_test_{i}",
                "index": i,
                "category": "even" if i % 2 == 0 else "odd",
                "created_at": datetime.utcnow(),
            }
            doc_ref = firestore_client.collection(test_collection).document(
                str(doc_data["test_id"])
            )
            doc_ref.set(doc_data)
            test_docs.append(doc_data["test_id"])

        try:
            # Test equality query
            query = firestore_client.collection(test_collection).where(
                "category", "==", "even"
            )
            results = list(query.stream())
            assert len(results) == 3  # 0, 2, 4 are even

            # Test range query
            query = firestore_client.collection(test_collection).where("index", ">=", 2)
            results = list(query.stream())
            assert len(results) == 3  # 2, 3, 4

            # Test ordering
            query = (
                firestore_client.collection(test_collection)
                .order_by("index", direction=firestore.Query.DESCENDING)
                .limit(2)
            )
            results = list(query.stream())
            assert len(results) == 2
            result0_dict = results[0].to_dict()
            assert result0_dict is not None
            assert result0_dict["index"] == 4
            result1_dict = results[1].to_dict()
            assert result1_dict is not None
            assert result1_dict["index"] == 3

        finally:
            # Clean up all test documents
            for doc_id in test_docs:
                try:
                    firestore_client.collection(test_collection).document(
                        str(doc_id)
                    ).delete()
                except (PermissionError, ConnectionError, ValueError, RuntimeError):
                    pass  # Cleanup failure is acceptable

    def test_transaction(
        self, firestore_client: firestore.Client, test_collection: str
    ) -> None:
        """Test transaction operations."""
        doc1_id = "transaction_test_1"
        doc2_id = "transaction_test_2"

        doc1_ref = firestore_client.collection(test_collection).document(doc1_id)
        doc2_ref = firestore_client.collection(test_collection).document(doc2_id)

        # Create initial documents
        doc1_ref.set({"counter": 0})
        doc2_ref.set({"counter": 10})

        try:

            @firestore.transactional
            def update_in_transaction(transaction: Any) -> None:
                # Read both documents
                doc1 = doc1_ref.get(transaction=transaction)
                doc2 = doc2_ref.get(transaction=transaction)

                # Update both documents
                doc1_data = doc1.to_dict()
                doc2_data = doc2.to_dict()
                assert doc1_data is not None
                assert doc2_data is not None
                new_value1 = doc1_data["counter"] + 5
                new_value2 = doc2_data["counter"] - 5

                transaction.update(doc1_ref, {"counter": new_value1})
                transaction.update(doc2_ref, {"counter": new_value2})

            # Execute transaction
            transaction = firestore_client.transaction()
            update_in_transaction(transaction)

            # Verify results
            doc1_result = doc1_ref.get().to_dict()
            doc2_result = doc2_ref.get().to_dict()
            assert doc1_result is not None
            assert doc2_result is not None
            assert doc1_result["counter"] == 5
            assert doc2_result["counter"] == 5

        finally:
            # Clean up
            doc1_ref.delete()
            doc2_ref.delete()
