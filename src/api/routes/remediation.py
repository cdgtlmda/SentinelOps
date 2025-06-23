"""Remediation API endpoints for SentinelOps."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from ..auth import Scopes, require_auth, require_scopes
from ..models.remediation import (
    RemediationAction,
    RemediationApprovalItem,
    RemediationApprovalResponse,
    RemediationExecutionRequest,
    RemediationExecutionResponse,
    RemediationHistoryResponse,
    RemediationRollbackRequest,
)
from ...common.models import RemediationPriority, RemediationStatus
from ...common.storage import Storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/remediation", tags=["Remediation"])


@router.get("/actions")
async def get_remediation_actions(
    incident_id: Optional[UUID] = Query(
        None, description="Filter actions by incident ID"
    ),
    status: Optional[RemediationStatus] = Query(
        None, description="Filter by remediation status"
    ),
    priority: Optional[RemediationPriority] = Query(
        None, description="Filter by priority"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of actions"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
) -> List[RemediationAction]:
    """Get available remediation actions.

    Args:
        incident_id: Optional incident ID filter
        status: Optional status filter
        priority: Optional priority filter
        limit: Maximum number of actions to return
        offset: Pagination offset
        auth: Authentication context

    Returns:
        List of remediation actions
    """
    try:
        storage = Storage()

        # Get all remediation actions
        all_actions = await storage.get_remediation_actions()

        # Apply filters
        filtered_actions = []
        for action in all_actions:
            if incident_id and action.incident_id != str(incident_id):
                continue
            if status and action.status != status:
                continue
            if priority and action.priority != priority:
                continue
            filtered_actions.append(action)

        # Apply pagination
        paginated_actions = filtered_actions[offset : offset + limit]

        logger.info(
            "Retrieved %d remediation actions (total: %d)",
            len(paginated_actions),
            len(filtered_actions),
        )

        return [
            RemediationAction.from_storage_model(action) for action in paginated_actions
        ]

    except Exception as e:
        logger.error("Failed to get remediation actions: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get remediation actions: {str(e)}"
        ) from e


@router.post("/execute")
async def execute_remediation(
    request: RemediationExecutionRequest,
    background_tasks: BackgroundTasks,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.REMEDIATION_EXECUTE])),
) -> RemediationExecutionResponse:
    """Execute a remediation action.

    Args:
        request: Remediation execution request
        background_tasks: FastAPI background tasks
        auth: Authentication context

    Returns:
        RemediationExecutionResponse with execution details
    """
    try:
        storage = Storage()

        # Validate the action exists
        action = await storage.get_remediation_action(str(request.action_id))
        if not action:
            raise HTTPException(
                status_code=404,
                detail=f"Remediation action {request.action_id} not found",
            )

        # Check if action requires approval
        if action.requires_approval and not request.approval_token:
            raise HTTPException(
                status_code=403,
                detail="This action requires approval. Please provide an approval token.",
            )

        # Validate approval token if provided
        if request.approval_token:
            approval = await storage.validate_approval_token(request.approval_token)
            if not approval or approval.get("action_id") != str(request.action_id):
                raise HTTPException(status_code=403, detail="Invalid approval token")

        # Create execution record
        execution_id = await storage.create_remediation_execution(
            action_id=str(request.action_id),
            executed_by=auth.get("sub", "unknown"),
            parameters=request.parameters,
            dry_run=request.dry_run,
        )

        # Execute in background
        background_tasks.add_task(
            _execute_remediation_async,
            execution_id,
            action,
            request.parameters,
            request.dry_run,
        )

        logger.info(
            "Started remediation execution %s for action %s",
            execution_id,
            request.action_id,
        )

        return RemediationExecutionResponse(
            execution_id=UUID(execution_id),
            action_id=request.action_id,
            status=RemediationStatus.PENDING,
            message="Remediation execution started",
            dry_run=request.dry_run,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute remediation: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to execute remediation: {str(e)}"
        ) from e


@router.get("/history")
async def get_remediation_history(
    incident_id: Optional[UUID] = Query(None, description="Filter by incident ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    status: Optional[RemediationStatus] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
) -> RemediationHistoryResponse:
    """Get remediation execution history.

    Args:
        incident_id: Optional incident ID filter
        action_type: Optional action type filter
        status: Optional status filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of records
        offset: Pagination offset
        auth: Authentication context

    Returns:
        RemediationHistoryResponse with execution history
    """
    try:
        storage = Storage()

        # Get remediation history
        history = await storage.get_remediation_history(
            incident_id=str(incident_id) if incident_id else None,
            action_type=action_type,
            status=status.value if status else None,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        total_count = await storage.count_remediation_history(
            incident_id=str(incident_id) if incident_id else None,
            action_type=action_type,
            status=status.value if status else None,
            start_date=start_date,
            end_date=end_date,
        )

        return RemediationHistoryResponse(
            executions=history,
            total=total_count,
            page=offset // limit + 1,
            page_size=limit,
            has_next=offset + limit < total_count,
        )

    except Exception as e:
        logger.error("Failed to get remediation history: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get remediation history: {str(e)}"
        ) from e


@router.post("/rollback")
async def rollback_remediation(
    request: RemediationRollbackRequest,
    background_tasks: BackgroundTasks,
    auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.REMEDIATION_EXECUTE])),
) -> Dict[str, Any]:
    """Rollback a remediation action.

    Args:
        request: Rollback request
        background_tasks: FastAPI background tasks
        auth: Authentication context

    Returns:
        Success response with rollback details
    """
    try:
        storage = Storage()

        # Validate the execution exists
        execution = await storage.get_remediation_execution(str(request.execution_id))
        if not execution:
            raise HTTPException(
                status_code=404,
                detail=f"Remediation execution {request.execution_id} not found",
            )

        # Check if already rolled back
        if execution.status == RemediationStatus.ROLLED_BACK:
            raise HTTPException(
                status_code=400, detail="This execution has already been rolled back"
            )

        # Check if rollback is possible
        if execution.status not in [
            RemediationStatus.COMPLETED,
            RemediationStatus.PARTIALLY_COMPLETED,
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot rollback execution in status: {execution.status}",
            )

        # Create rollback record
        rollback_id = await storage.create_remediation_rollback(
            execution_id=str(request.execution_id),
            reason=request.reason,
            initiated_by=auth.get("sub", "unknown"),
        )

        # Execute rollback in background
        background_tasks.add_task(
            _execute_rollback_async, rollback_id, execution, request.force
        )

        logger.info(
            "Started rollback %s for execution %s", rollback_id, request.execution_id
        )

        return {
            "rollback_id": rollback_id,
            "execution_id": request.execution_id,
            "status": "rollback_initiated",
            "message": "Rollback process started",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to rollback remediation: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to rollback remediation: {str(e)}"
        ) from e


@router.get("/approval-queue")
async def get_approval_queue(
    status: Optional[str] = Query("pending", description="Approval status filter"),
    priority: Optional[RemediationPriority] = Query(
        None, description="Priority filter"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items"),
    _auth: Dict[str, Any] = Depends(require_auth),
    _: None = Depends(require_scopes([Scopes.INCIDENTS_READ])),
) -> RemediationApprovalResponse:
    """Get remediation actions pending approval.

    Args:
        status: Approval status filter (pending, approved, rejected)
        priority: Optional priority filter
        limit: Maximum number of items
        auth: Authentication context

    Returns:
        RemediationApprovalResponse with pending approvals
    """
    try:
        storage = Storage()

        # Get approval queue
        approval_items = await storage.get_approval_queue(
            status=status, priority=priority.value if priority else None, limit=limit
        )

        # Convert to response models
        items = []
        for item in approval_items:
            items.append(
                RemediationApprovalItem(
                    approval_id=item.id,
                    action_id=item.action_id,
                    incident_id=item.incident_id,
                    action_type=item.action_type,
                    description=item.description,
                    priority=item.priority,
                    risk_level=item.risk_level,
                    requested_by=item.requested_by,
                    requested_at=item.requested_at,
                    approval_status=item.status,
                    approved_by=item.approved_by,
                    approved_at=item.approved_at,
                    rejection_reason=item.rejection_reason,
                )
            )

        return RemediationApprovalResponse(
            items=items,
            total=len(items),
            pending_count=sum(1 for i in items if i.approval_status == "pending"),
        )

    except (OSError, ConnectionError, RuntimeError, ValueError) as e:
        logger.error("Failed to get approval queue: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get approval queue: {str(e)}"
        ) from e


async def _execute_remediation_async(
    execution_id: str,
    _action: Any,
    _parameters: Dict[str, Any],
    dry_run: bool,
) -> None:
    """Execute remediation action asynchronously.

    This is a simplified implementation. In production, this would
    integrate with the actual remediation agent.
    """
    storage = Storage()

    try:
        # Update status to executing
        await storage.update_remediation_execution(
            execution_id, status=RemediationStatus.EXECUTING
        )

        # Simulate execution
        logger.info("Executing remediation %s (dry_run=%s)", execution_id, dry_run)

        if dry_run:
            # Simulate dry run
            result = {
                "dry_run": True,
                "simulated_changes": [
                    "Would block IP addresses: 192.168.1.100, 10.0.0.50",
                    "Would disable user accounts: user123, admin456",
                    "Would update firewall rules",
                ],
                "estimated_impact": "High",
                "warnings": [],
            }
        else:
            # In production, this would call the actual remediation logic
            result = {
                "executed": True,
                "changes_made": [
                    "Blocked 2 IP addresses",
                    "Disabled 2 user accounts",
                    "Updated 3 firewall rules",
                ],
                "execution_time_seconds": 15.3,
            }

        # Update execution status
        await storage.update_remediation_execution(
            execution_id,
            status=RemediationStatus.COMPLETED,
            result=result,
            completed_at=datetime.now(timezone.utc),
        )

        logger.info("Completed remediation execution %s", execution_id)

    except (OSError, ConnectionError, RuntimeError, ValueError) as e:
        logger.error("Failed to execute remediation %s: %s", execution_id, str(e))
        await storage.update_remediation_execution(
            execution_id,
            status=RemediationStatus.FAILED,
            error=str(e),
            completed_at=datetime.now(timezone.utc),
        )


async def _execute_rollback_async(
    rollback_id: str, execution: Any, force: bool
) -> None:
    """Execute rollback asynchronously.

    This is a simplified implementation. In production, this would
    integrate with the actual remediation agent.
    """
    storage = Storage()

    try:
        # Update rollback status
        await storage.update_remediation_rollback(
            rollback_id, status=RemediationStatus.EXECUTING
        )

        # Simulate rollback
        logger.info("Executing rollback %s (force=%s)", rollback_id, force)

        # In production, this would perform actual rollback
        result = {
            "rolled_back": True,
            "changes_reverted": [
                "Unblocked 2 IP addresses",
                "Re-enabled 2 user accounts",
                "Restored 3 firewall rules",
            ],
            "rollback_time_seconds": 12.1,
        }

        # Update rollback status
        await storage.update_remediation_rollback(
            rollback_id,
            status=RemediationStatus.COMPLETED,
            result=result,
            completed_at=datetime.now(timezone.utc),
        )

        # Update original execution status
        await storage.update_remediation_execution(
            execution.id, status=RemediationStatus.ROLLED_BACK
        )

        logger.info("Completed rollback %s", rollback_id)

    except (OSError, ConnectionError, RuntimeError, ValueError) as e:
        logger.error("Failed to execute rollback %s: %s", rollback_id, str(e))
        await storage.update_remediation_rollback(
            rollback_id,
            status=RemediationStatus.FAILED,
            error=str(e),
            completed_at=datetime.now(timezone.utc),
        )
