"""
Natural Language Processing API Routes

This module provides API endpoints for natural language queries and conversational
interfaces using the Gemini integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.api.auth_routes import get_current_user
# from src.api.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nlp", tags=["Natural Language Processing"])


def get_gemini(request: Request) -> Any:
    """Get Gemini integration from app state"""
    return request.app.state.gemini


class NaturalQueryRequest(BaseModel):
    """Request model for natural language queries"""

    query: str = Field(..., description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Optional context for the query"
    )
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for multi-turn conversations"
    )


class NaturalQueryResponse(BaseModel):
    """Response model for natural language queries"""

    query: str
    response: str
    intent: str
    confidence: float
    conversation_id: Optional[str]
    follow_up_questions: Optional[List[str]]
    timestamp: str


class ConversationSummaryRequest(BaseModel):
    """Request model for conversation summary"""

    conversation_id: str = Field(..., description="Conversation ID to summarize")


class IncidentExplanationRequest(BaseModel):
    """Request model for incident explanation"""

    incident_summary: str = Field(..., description="Incident summary to explain")
    user_level: str = Field(
        "technical",
        description="Target audience level: executive, technical, or general",
    )


class RecommendationClarificationRequest(BaseModel):
    """Request model for recommendation clarification"""

    recommendation: str = Field(..., description="Original recommendation")
    clarification_request: str = Field(..., description="What needs clarification")


class ValidatedQueryRequest(BaseModel):
    """Request model for validated natural language queries"""

    query: str = Field(..., description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context")
    require_fact_check: bool = Field(False, description="Enable fact checking")
    safety_level: str = Field(
        "standard", description="Safety level: strict, standard, or relaxed"
    )


# In-memory conversation storage (would typically use a database)
conversations: Dict[str, List[Dict[str, Any]]] = {}


@router.post("/query", response_model=NaturalQueryResponse)
async def process_natural_query(
    request: NaturalQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    gemini: Any = Depends(get_gemini),
) -> NaturalQueryResponse:
    """
    Process a natural language query about security incidents or system status

    Args:
        request: Natural language query request
        current_user: Authenticated user

    Returns:
        Query response with intent and optional follow-up questions
    """
    try:
        # Process the query
        result = await gemini.process_natural_query(
            query=request.query, context=request.context
        )

        # Generate conversation ID if not provided
        conversation_id = (
            request.conversation_id or f"conv_{datetime.now().timestamp()}"
        )

        # Store in conversation history
        if conversation_id not in conversations:
            conversations[conversation_id] = []

        conversations[conversation_id].append(
            {
                "question": request.query,
                "answer": result["response"],
                "timestamp": result["timestamp"],
                "user": current_user["username"],
            }
        )

        # Get follow-up questions if this is part of a conversation
        follow_up_questions = []
        if len(conversations[conversation_id]) > 1:
            follow_up_questions = await gemini.suggest_follow_up_questions(
                conversation_history=conversations[conversation_id],
                current_topic=request.query,
            )

        return NaturalQueryResponse(
            query=request.query,
            response=result["response"],
            intent=result["intent"],
            confidence=0.85,  # Placeholder - would come from validation
            conversation_id=conversation_id,
            follow_up_questions=follow_up_questions,
            timestamp=result["timestamp"],
        )

    except Exception as e:
        logger.error("Error processing natural query: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/query/validated", response_model=Dict[str, Any])
async def process_validated_query(
    request: ValidatedQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    gemini: Any = Depends(get_gemini),
) -> Dict[str, Any]:
    """
    Process a natural language query with validation and safety checks

    Args:
        request: Validated query request
        current_user: Authenticated user

    Returns:
        Query response with validation results
    """
    try:
        # Build prompt for natural language processing
        prompt = f"""User Query: {request.query}

Context: {request.context if request.context else 'No additional context provided'}

Please provide a helpful response to this security-related query."""

        # Generate with validation
        result = await gemini.generate_with_validation(
            prompt=prompt,
            fact_check_context=request.context if request.require_fact_check else None,
            safety_level=request.safety_level,
        )

        # Add user info for audit
        result["user"] = current_user["username"]
        result["query"] = request.query

        return dict(result)

    except Exception as e:
        logger.error("Error processing validated query: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/explain/incident")
async def explain_incident(
    request: IncidentExplanationRequest,
    gemini: Any = Depends(get_gemini),
) -> Dict[str, Any]:
    """
    Generate a user-friendly explanation of a security incident

    Args:
        request: Incident explanation request
        current_user: Authenticated user

    Returns:
        Explanation tailored to the specified user level
    """
    try:
        explanation = await gemini.generate_incident_explanation(
            incident_summary=request.incident_summary, user_level=request.user_level
        )

        return {
            "incident_summary": request.incident_summary,
            "explanation": explanation,
            "user_level": request.user_level,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error("Error generating incident explanation: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/clarify/recommendation")
async def clarify_recommendation(
    request: RecommendationClarificationRequest,
    gemini: Any = Depends(get_gemini),
) -> Dict[str, Any]:
    """
    Provide clarification on a security recommendation

    Args:
        request: Recommendation clarification request
        current_user: Authenticated user

    Returns:
        Clarified explanation
    """
    try:
        clarification = await gemini.clarify_recommendation(
            recommendation=request.recommendation,
            clarification_request=request.clarification_request,
        )

        return {
            "original_recommendation": request.recommendation,
            "clarification_request": request.clarification_request,
            "clarification": clarification,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error("Error generating clarification: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/conversation/summary")
async def summarize_conversation(
    request: ConversationSummaryRequest,
    gemini: Any = Depends(get_gemini),
) -> Dict[str, Any]:
    """
    Summarize a security conversation

    Args:
        request: Conversation summary request
        current_user: Authenticated user

    Returns:
        Conversation summary with key points
    """
    try:
        # Get conversation history
        if request.conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")

        history = conversations[request.conversation_id]

        # Generate summary
        summary = await gemini.summarize_conversation(history)

        return {
            "conversation_id": request.conversation_id,
            "summary": summary,
            "message_count": len(history),
            "generated_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error summarizing conversation: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/conversation/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get conversation history

    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user

    Returns:
        Conversation history
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = conversations[conversation_id]

    # Filter by user if not admin
    if current_user.get("role") != "admin":
        history = [
            msg for msg in history if msg.get("user") == current_user["username"]
        ]

    return {
        "conversation_id": conversation_id,
        "history": history,
        "message_count": len(history),
    }


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a conversation

    Args:
        conversation_id: Conversation ID to delete
        current_user: Authenticated user

    Returns:
        Deletion confirmation
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check ownership or admin
    history = conversations[conversation_id]
    if current_user.get("role") != "admin":
        # Check if user owns all messages
        if not all(msg.get("user") == current_user["username"] for msg in history):
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this conversation"
            )

    del conversations[conversation_id]

    return {
        "conversation_id": conversation_id,
        "deleted": True,
        "deleted_at": datetime.now().isoformat(),
    }


@router.post("/safety/add-filter")
async def add_content_filter(
    filter_config: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    gemini: Any = Depends(get_gemini),
) -> Dict[str, Any]:
    """
    Add a content filter (admin only)

    Args:
        filter_config: Filter configuration
        current_user: Authenticated user (must be admin)

    Returns:
        Confirmation
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # This is a simplified example - in production, you'd parse and validate the filter config
    def filter_func(response: str) -> str:
        # Example: redact sensitive patterns
        patterns = filter_config.get("patterns", [])
        filtered = response
        for pattern in patterns:
            filtered = filtered.replace(pattern, "[REDACTED]")
        return filtered

    gemini.add_content_filter(filter_func)

    return {
        "filter_added": True,
        "config": filter_config,
        "added_at": datetime.now().isoformat(),
    }


@router.post("/safety/set-threshold")
async def set_confidence_threshold(
    threshold: float,
    current_user: Dict[str, Any] = Depends(get_current_user),
    gemini: Any = Depends(get_gemini),
) -> Dict[str, Any]:
    """
    Set confidence threshold (admin only)

    Args:
        threshold: New confidence threshold (0.0 to 1.0)
        current_user: Authenticated user (must be admin)

    Returns:
        Confirmation
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if not 0.0 <= threshold <= 1.0:
        raise HTTPException(
            status_code=400, detail="Threshold must be between 0.0 and 1.0"
        )

    gemini.set_confidence_threshold(threshold)

    return {"threshold_set": threshold, "updated_at": datetime.now().isoformat()}
