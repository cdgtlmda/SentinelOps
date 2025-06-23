"""
Database operations for rules.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.rules import (
    RuleCreate,
    RuleSeverity,
    RuleStatus,
    RuleType,
    RuleUpdate,
)
from src.database.models.rules import RuleModel


class RulesRepository:
    """Repository for rule database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self, rule_data: RuleCreate, created_by: str, rule_number: str
    ) -> RuleModel:
        """Create a new rule in the database."""
        rule = RuleModel(
            rule_number=rule_number,
            name=rule_data.name,
            description=rule_data.description,
            rule_type=rule_data.rule_type,
            severity=rule_data.severity,
            status=RuleStatus.ACTIVE,
            query=rule_data.query,
            conditions=(
                [c.model_dump() for c in rule_data.conditions]
                if rule_data.conditions
                else None
            ),
            threshold=rule_data.threshold.model_dump() if rule_data.threshold else None,
            correlation=(
                rule_data.correlation.model_dump() if rule_data.correlation else None
            ),
            enabled=rule_data.enabled,
            tags=rule_data.tags,
            references=rule_data.references,
            false_positive_rate=rule_data.false_positive_rate,
            actions=[a.model_dump() for a in rule_data.actions],
            custom_fields=rule_data.custom_fields,
            created_by=created_by,
            updated_by=created_by,
        )

        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def get_by_id(self, rule_id: UUID) -> Optional[RuleModel]:
        """Get a rule by ID."""
        result = await self.session.execute(
            select(RuleModel).where(RuleModel.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_rule_number(self, rule_number: str) -> Optional[RuleModel]:
        """Get a rule by rule number."""
        result = await self.session.execute(
            select(RuleModel).where(RuleModel.rule_number == rule_number)
        )
        return result.scalar_one_or_none()

    async def list_rules(
        self,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[RuleStatus] = None,
        type_filter: Optional[RuleType] = None,
        severity_filter: Optional[RuleSeverity] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = False,
        created_by: Optional[str] = None,
        count_total: bool = True,
    ) -> tuple[list[RuleModel], int]:
        """
        List rules with optional filtering and pagination.

        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return
            status_filter: Filter by rule status
            type_filter: Filter by rule type
            severity_filter: Filter by rule severity
            search: Search term for rule names/descriptions
            tags: Filter by tags (rule must have all tags)
            enabled_only: Only return enabled rules
            created_by: Filter by creator
            count_total: Whether to count total results

        Returns:
            Tuple of (rules list, total count)
        """
        query = select(RuleModel)

        # Apply filters
        if status_filter:
            query = query.where(RuleModel.status == status_filter)

        if type_filter:
            query = query.where(RuleModel.rule_type == type_filter)

        if severity_filter:
            query = query.where(RuleModel.severity == severity_filter)

        if enabled_only:
            query = query.where(RuleModel.enabled.is_(True))

        if created_by:
            query = query.where(RuleModel.created_by == created_by)

        if search:
            search_filter = or_(
                RuleModel.name.ilike(f"%{search}%"),
                RuleModel.description.ilike(f"%{search}%"),
                RuleModel.rule_number.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        if tags:
            for tag in tags:
                query = query.where(RuleModel.tags.contains([tag]))

        # Get total count if requested
        if count_total:
            count_result = await self.session.execute(
                select(func.count()).select_from(query.subquery())  # pylint: disable=not-callable
            )
            total = count_result.scalar() or 0
        else:
            total = 0

        # Apply pagination and ordering
        query = query.order_by(RuleModel.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        rules = list(result.scalars().all())

        return rules, total

    async def update(
        self, rule_id: UUID, rule_update: RuleUpdate, updated_by: str
    ) -> Optional[RuleModel]:
        """Update a rule."""
        rule = await self.get_by_id(rule_id)
        if not rule:
            return None

        # Update fields if provided
        update_data = rule_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "conditions" and value is not None:
                value = [c.model_dump() for c in value]
            elif field == "threshold" and value is not None:
                value = value.model_dump()
            elif field == "correlation" and value is not None:
                value = value.model_dump()
            elif field == "actions" and value is not None:
                value = [a.model_dump() for a in value]

            setattr(rule, field, value)

        rule.updated_by = updated_by  # type: ignore[assignment]
        rule.version += 1  # type: ignore[assignment]
        rule.updated_at = datetime.utcnow()  # type: ignore[assignment]

        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def delete(self, rule_id: UUID) -> bool:
        """Delete a rule."""
        rule = await self.get_by_id(rule_id)
        if not rule:
            return False

        await self.session.delete(rule)
        await self.session.commit()
        return True

    async def update_metrics(
        self, rule_id: UUID, metrics: Dict[str, Any]
    ) -> Optional[RuleModel]:
        """Update rule metrics."""
        rule = await self.get_by_id(rule_id)
        if not rule:
            return None

        rule.metrics = metrics  # type: ignore[assignment]
        rule.last_executed = datetime.utcnow()  # type: ignore[assignment]

        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def update_status(
        self, rule_id: UUID, status: RuleStatus, updated_by: str
    ) -> Optional[RuleModel]:
        """Update rule status."""
        rule = await self.get_by_id(rule_id)
        if not rule:
            return None

        rule.status = status  # type: ignore[assignment]
        rule.updated_by = updated_by  # type: ignore[assignment]
        rule.updated_at = datetime.utcnow()  # type: ignore[assignment]

        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def get_next_rule_number(self) -> str:
        """Generate the next rule number."""
        # Get the highest rule number
        result = await self.session.execute(select(func.max(RuleModel.rule_number)))
        max_rule_number = result.scalar()

        if not max_rule_number:
            return "RULE-000001"

        # Extract the number part and increment
        try:
            current_num = int(max_rule_number.split("-")[1])
            next_num = current_num + 1
            return f"RULE-{next_num:06d}"
        except (IndexError, ValueError):
            # Fallback if format is unexpected
            return "RULE-000001"
