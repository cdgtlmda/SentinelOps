"""
ADK Session Management for SentinelOps

This module provides session management capabilities for the multi-agent system
using ADK's session patterns.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, cast
from uuid import uuid4

from google.adk.sessions import Session, InMemorySessionService
from google.cloud import firestore

logger = logging.getLogger(__name__)


class SentinelOpsSessionManager:
    """Session manager for SentinelOps multi-agent system.

    Manages agent sessions, state persistence, and inter-agent context sharing.
    """

    def __init__(self, project_id: str, use_firestore: bool = True):
        """Initialize the session manager.

        Args:
            project_id: Google Cloud project ID
            use_firestore: Whether to use Firestore for persistence
        """
        self.project_id = project_id
        self.use_firestore = use_firestore

        # Initialize ADK session service
        self.session_service = InMemorySessionService()  # type: ignore[no-untyped-call]

        # Initialize Firestore client if enabled
        if use_firestore:
            try:
                self.firestore_client = firestore.Client(project=project_id)
                self.sessions_collection = self.firestore_client.collection(
                    "agent_sessions"
                )
                logger.info("Initialized Firestore-backed session management")
            except (ValueError, ImportError, RuntimeError, AttributeError) as e:
                logger.warning("Could not initialize Firestore: %s", e)
                self.use_firestore = False

    def create_session(self, session_id: Optional[str] = None) -> Session:
        """Create a new agent session.

        Args:
            session_id: Optional session ID (auto-generated if not provided)

        Returns:
            New Session instance
        """
        if not session_id:
            session_id = f"session_{uuid4().hex[:12]}"

        # Create ADK session using session service
        session = self.session_service.create_session_sync(
            app_name="sentinelops",
            user_id=f"user_{self.project_id}",
            state={
                "created_at": datetime.utcnow().isoformat(),
                "project_id": self.project_id,
                "agent_hierarchy": self._get_agent_hierarchy(),
            },
            session_id=session_id,
        )

        # Persist to Firestore if enabled
        if self.use_firestore:
            self._persist_session(session)

        logger.info("Created session: %s", session_id)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session instance or None if not found
        """
        # Try in-memory first
        session = self.session_service.get_session_sync(
            app_name="sentinelops",
            user_id=f"user_{self.project_id}",
            session_id=session_id,
        )

        # Try Firestore if not found in memory
        if not session and self.use_firestore:
            session = self._load_session_from_firestore(session_id)
            if session:
                # Session is already loaded, no need to store in memory again
                # The InMemorySessionService manages its own storage
                pass

        return session

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data.

        Args:
            session_id: Session identifier
            updates: Data to update

        Returns:
            Success status
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning("Session not found: %s", session_id)
            return False

        # Update state by recreating the session with new state
        session.state.update(updates)
        session.state["updated_at"] = datetime.utcnow().isoformat()

        # Delete the old session and create a new one with updated state
        try:
            self.session_service.delete_session_sync(
                app_name="sentinelops",
                user_id=f"user_{self.project_id}",
                session_id=session_id,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass  # Ignore if session doesn't exist

        # Create new session with updated state
        self.session_service.create_session_sync(
            app_name="sentinelops",
            user_id=f"user_{self.project_id}",
            state=session.state,
            session_id=session_id,
        )

        # Persist to Firestore
        if self.use_firestore:
            self._persist_session(session)

        return True

    def add_agent_context(
        self, session_id: str, agent_name: str, context: Dict[str, Any]
    ) -> bool:
        """Add agent-specific context to session.

        Args:
            session_id: Session identifier
            agent_name: Name of the agent
            context: Context data to add

        Returns:
            Success status
        """
        # Get current session to preserve existing agent contexts
        session = self.get_session(session_id)
        if not session:
            return False

        # Ensure agent_contexts exists in state
        if "agent_contexts" not in session.state:
            session.state["agent_contexts"] = {}

        # Add the agent context
        session.state["agent_contexts"][agent_name] = {
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Update the session with the modified state
        updates = {"agent_contexts": session.state["agent_contexts"]}
        return self.update_session(session_id, updates)

    def get_agent_context(
        self, session_id: str, agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get agent-specific context from session.

        Args:
            session_id: Session identifier
            agent_name: Name of the agent

        Returns:
            Agent context or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        agent_contexts = session.state.get("agent_contexts", {})
        agent_data = agent_contexts.get(agent_name, {})
        context = agent_data.get("context")
        return cast(Optional[Dict[str, Any]], context)

    def cleanup_old_sessions(self, older_than_hours: int = 24) -> None:
        """Clean up old sessions.

        Args:
            older_than_hours: Age threshold in hours
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

        if self.use_firestore:
            try:
                # Query old sessions
                old_sessions = self.sessions_collection.where(
                    "created_at", "<", cutoff_time.isoformat()
                ).stream()

                count = 0
                for doc in old_sessions:
                    doc.reference.delete()
                    count += 1

                logger.info("Cleaned up %d old sessions", count)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Error cleaning up sessions: %s", e)

    def _get_agent_hierarchy(self) -> Dict[str, Any]:
        """Get the agent hierarchy configuration.

        Returns:
            Agent hierarchy structure
        """
        return {
            "coordinator": {
                "name": "sentinelops_coordinator",
                "type": "ParallelAgent",
                "sub_agents": {
                    "orchestrator": {
                        "name": "orchestrator_agent",
                        "type": "SequentialAgent",
                        "role": "primary_coordinator",
                        "manages": [
                            "detection",
                            "analysis",
                            "remediation",
                            "communication",
                        ],
                    },
                    "detection": {
                        "name": "detection_agent",
                        "type": "LlmAgent",
                        "role": "continuous_monitoring",
                    },
                    "analysis": {
                        "name": "analysis_agent",
                        "type": "LlmAgent",
                        "role": "incident_analysis",
                        "model": "gemini-pro",
                    },
                    "remediation": {
                        "name": "remediation_agent",
                        "type": "LlmAgent",
                        "role": "response_actions",
                        "requires_approval": True,
                    },
                    "communication": {
                        "name": "communication_agent",
                        "type": "LlmAgent",
                        "role": "notifications",
                    },
                },
            }
        }

    def _persist_session(self, session: Session) -> None:
        """Persist session to Firestore.

        Args:
            session: Session to persist
        """
        try:
            doc_ref = self.sessions_collection.document(session.id)
            doc_ref.set(
                {
                    "session_id": session.id,
                    "state": session.state,
                    "created_at": session.state.get("created_at"),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error persisting session: %s", e)

    def _load_session_from_firestore(self, session_id: str) -> Optional[Session]:
        """Load session from Firestore.

        Args:
            session_id: Session identifier

        Returns:
            Session instance or None
        """
        try:
            doc_ref = self.sessions_collection.document(session_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                session = Session(
                    id=session_id,
                    app_name="sentinelops",
                    user_id=f"user_{self.project_id}",
                    state=data.get("state", {}),
                )
                return session
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error loading session: %s", e)

        return None
