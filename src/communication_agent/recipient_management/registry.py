"""
Recipient registry for managing notification recipients.

Provides storage and retrieval of recipients, contact information,
escalation chains, and on-call schedules.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.communication_agent.recipient_management.models import (
    ContactInfo,
    EscalationChain,
    EscalationLevel,
    NotificationPreferences,
    OnCallSchedule,
    Recipient,
    RecipientRole,
)
from src.communication_agent.types import NotificationChannel
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RecipientRegistry:
    """Registry for managing notification recipients."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize recipient registry.

        Args:
            storage_path: Path to store registry data
        """
        self.storage_path = storage_path
        self.recipients: Dict[str, Recipient] = {}
        self.escalation_chains: Dict[str, EscalationChain] = {}
        self.on_call_schedules: Dict[str, OnCallSchedule] = {}
        self.preferences: Dict[str, NotificationPreferences] = {}

        # Load data if storage path exists
        if self.storage_path and self.storage_path.exists():
            self._load_from_storage()
        else:
            self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Initialize with default recipients and configurations."""
        # Add default security team recipient
        security_team = Recipient(
            id="security-team",
            name="Security Team",
            role=RecipientRole.SECURITY_ENGINEER,
            contacts=[
                ContactInfo(
                    channel=NotificationChannel.EMAIL,
                    address="security@example.com",
                    verified=True,
                    preferred=True,
                ),
                ContactInfo(
                    channel=NotificationChannel.SLACK,
                    address="#security-alerts",
                    verified=True,
                ),
            ],
            tags={"team", "security", "default"},
        )
        self.add_recipient(security_team)

        # Add default escalation chain
        default_escalation = EscalationChain(
            id="default-escalation",
            name="Default Incident Escalation",
            description="Standard escalation chain for security incidents",
            levels=[
                EscalationLevel(
                    level=1,
                    recipients=["security-team"],
                    delay_minutes=0,
                ),
                EscalationLevel(
                    level=2,
                    recipients=["on-call-primary"],
                    delay_minutes=15,
                ),
                EscalationLevel(
                    level=3,
                    recipients=["security-manager", "on-call-secondary"],
                    delay_minutes=30,
                ),
            ],
            tags={"default", "incident"},
        )
        self.add_escalation_chain(default_escalation)

        logger.info("Initialized recipient registry with defaults")

    def add_recipient(self, recipient: Recipient) -> None:
        """Add a recipient to the registry."""
        if recipient.id in self.recipients:
            raise ValueError(f"Recipient {recipient.id} already exists")

        self.recipients[recipient.id] = recipient

        # Create default preferences if not exist
        if recipient.id not in self.preferences:
            self.preferences[recipient.id] = NotificationPreferences(
                recipient_id=recipient.id,
                timezone=recipient.timezone,
            )

        logger.info(
            "Added recipient: %s",
            recipient.id,
            extra={
                "recipient_name": recipient.name,
                "role": recipient.role.value,
                "contacts": len(recipient.contacts),
            },
        )

        self._save_to_storage()

    def get_recipient(self, recipient_id: str) -> Optional[Recipient]:
        """Get a recipient by ID."""
        return self.recipients.get(recipient_id)

    def find_recipients_by_role(self, role: RecipientRole) -> List[Recipient]:
        """Find all recipients with a specific role."""
        return [r for r in self.recipients.values() if r.role == role]

    def find_recipients_by_tag(self, tag: str) -> List[Recipient]:
        """Find all recipients with a specific tag."""
        return [r for r in self.recipients.values() if tag in r.tags]

    def find_recipients_by_channel(
        self,
        channel: NotificationChannel,
    ) -> List[Recipient]:
        """Find all recipients with a specific channel configured."""
        recipients = []
        for recipient in self.recipients.values():
            if recipient.get_contact_for_channel(channel):
                recipients.append(recipient)
        return recipients

    def update_recipient(self, recipient: Recipient) -> None:
        """Update a recipient in the registry."""
        if recipient.id not in self.recipients:
            raise ValueError(f"Recipient {recipient.id} not found")

        recipient.updated_at = datetime.now(timezone.utc)
        self.recipients[recipient.id] = recipient

        logger.info(
            "Updated recipient: %s",
            recipient.id,
            extra={"recipient_name": recipient.name},
        )

        self._save_to_storage()

    def remove_recipient(self, recipient_id: str) -> bool:
        """Remove a recipient from the registry."""
        if recipient_id in self.recipients:
            del self.recipients[recipient_id]

            # Remove from escalation chains
            for chain in self.escalation_chains.values():
                for level in chain.levels:
                    if recipient_id in level.recipients:
                        level.recipients.remove(recipient_id)

            # Remove from on-call schedules
            for schedule in self.on_call_schedules.values():
                schedule.remove_shifts_for_recipient(recipient_id)

            # Remove preferences
            if recipient_id in self.preferences:
                del self.preferences[recipient_id]

            logger.info("Removed recipient: %s", recipient_id)
            self._save_to_storage()
            return True

        return False

    def add_escalation_chain(self, chain: EscalationChain) -> None:
        """Add an escalation chain."""
        if chain.id in self.escalation_chains:
            raise ValueError(f"Escalation chain {chain.id} already exists")

        self.escalation_chains[chain.id] = chain

        logger.info(
            "Added escalation chain: %s",
            chain.id,
            extra={
                "chain_name": chain.name,
                "levels": len(chain.levels),
            },
        )

        self._save_to_storage()

    def get_escalation_chain(self, chain_id: str) -> Optional[EscalationChain]:
        """Get an escalation chain by ID."""
        return self.escalation_chains.get(chain_id)

    def add_on_call_schedule(self, schedule: OnCallSchedule) -> None:
        """Add an on-call schedule."""
        if schedule.id in self.on_call_schedules:
            raise ValueError(f"On-call schedule {schedule.id} already exists")

        self.on_call_schedules[schedule.id] = schedule

        logger.info(
            "Added on-call schedule: %s",
            schedule.id,
            extra={
                "schedule_name": schedule.name,
                "shifts": len(schedule.shifts),
            },
        )

        self._save_to_storage()

    def get_on_call_schedule(self, schedule_id: str) -> Optional[OnCallSchedule]:
        """Get an on-call schedule by ID."""
        return self.on_call_schedules.get(schedule_id)

    def get_current_on_call(
        self,
        schedule_id: Optional[str] = None,
        primary_only: bool = False,
    ) -> List[Recipient]:
        """Get current on-call recipients."""
        recipients = []

        if schedule_id:
            # Get from specific schedule
            schedule = self.get_on_call_schedule(schedule_id)
            if schedule:
                recipients.extend(
                    self._get_recipients_from_schedule(schedule, primary_only)
                )
        else:
            # Get from all schedules
            for schedule in self.on_call_schedules.values():
                recipients.extend(
                    self._get_recipients_from_schedule(schedule, primary_only)
                )

        return self._remove_duplicate_recipients(recipients)

    def _get_recipients_from_schedule(
        self,
        schedule: OnCallSchedule,
        primary_only: bool,
    ) -> List[Recipient]:
        """Get available recipients from an on-call schedule."""
        recipients = []
        if schedule.enabled:
            recipient_ids = schedule.get_current_on_call(primary_only)
            for rid in recipient_ids:
                recipient = self.get_recipient(rid)
                if recipient and recipient.is_available():
                    recipients.append(recipient)
        return recipients

    def _remove_duplicate_recipients(
        self,
        recipients: List[Recipient],
    ) -> List[Recipient]:
        """Remove duplicate recipients while preserving order."""
        seen = set()
        unique_recipients = []
        for r in recipients:
            if r.id not in seen:
                seen.add(r.id)
                unique_recipients.append(r)
        return unique_recipients

    def get_preferences(self, recipient_id: str) -> Optional[NotificationPreferences]:
        """Get notification preferences for a recipient."""
        return self.preferences.get(recipient_id)

    def update_preferences(self, preferences: NotificationPreferences) -> None:
        """Update notification preferences."""
        self.preferences[preferences.recipient_id] = preferences

        logger.info(
            "Updated preferences for recipient: %s",
            preferences.recipient_id,
            extra={
                "quiet_hours_enabled": preferences.quiet_hours_enabled,
                "severity_threshold": preferences.severity_threshold,
            },
        )

        self._save_to_storage()

    def resolve_recipients(
        self,
        recipient_specs: List[Dict[str, Any]],
    ) -> List[Tuple[Recipient, NotificationChannel, str]]:
        """
        Resolve recipient specifications to actual recipients.

        Args:
            recipient_specs: List of recipient specifications

        Returns:
            List of (recipient, channel, address) tuples
        """
        resolved = []

        for spec in recipient_specs:
            resolved.extend(self._resolve_single_spec(spec))

        return resolved

    def _resolve_single_spec(
        self,
        spec: Dict[str, Any],
    ) -> List[Tuple[Recipient, NotificationChannel, str]]:
        """Resolve a single recipient specification."""
        if "recipient_id" in spec:
            return self._resolve_by_recipient_id(spec)
        elif "role" in spec:
            return self._resolve_by_role(spec)
        elif "tag" in spec:
            return self._resolve_by_tag(spec)
        elif "on_call" in spec:
            return self._resolve_by_on_call(spec)
        elif "channel" in spec and "address" in spec:
            return self._resolve_direct_address(spec)
        return []

    def _resolve_by_recipient_id(
        self,
        spec: Dict[str, Any],
    ) -> List[Tuple[Recipient, NotificationChannel, str]]:
        """Resolve by direct recipient ID."""
        resolved = []
        recipient = self.get_recipient(spec["recipient_id"])
        if recipient:
            channel = NotificationChannel(spec.get("channel", "email"))
            contact = recipient.get_contact_for_channel(channel)
            if contact:
                resolved.append((recipient, channel, contact.address))
        return resolved

    def _resolve_by_role(
        self,
        spec: Dict[str, Any],
    ) -> List[Tuple[Recipient, NotificationChannel, str]]:
        """Resolve by role-based routing."""
        resolved = []
        role = RecipientRole(spec["role"])
        channel = NotificationChannel(spec.get("channel", "email"))
        recipients = self.find_recipients_by_role(role)
        for recipient in recipients:
            contact = recipient.get_contact_for_channel(channel)
            if contact:
                resolved.append((recipient, channel, contact.address))
        return resolved

    def _resolve_by_tag(
        self,
        spec: Dict[str, Any],
    ) -> List[Tuple[Recipient, NotificationChannel, str]]:
        """Resolve by tag-based routing."""
        resolved = []
        tag = spec["tag"]
        channel = NotificationChannel(spec.get("channel", "email"))
        recipients = self.find_recipients_by_tag(tag)
        for recipient in recipients:
            contact = recipient.get_contact_for_channel(channel)
            if contact:
                resolved.append((recipient, channel, contact.address))
        return resolved

    def _resolve_by_on_call(
        self,
        spec: Dict[str, Any],
    ) -> List[Tuple[Recipient, NotificationChannel, str]]:
        """Resolve by on-call routing."""
        resolved = []
        schedule_id = spec.get("schedule_id")
        primary_only = spec.get("primary_only", False)
        channel = NotificationChannel(spec.get("channel", "email"))
        recipients = self.get_current_on_call(schedule_id, primary_only)
        for recipient in recipients:
            contact = recipient.get_contact_for_channel(channel)
            if contact:
                resolved.append((recipient, channel, contact.address))
        return resolved

    def _resolve_direct_address(
        self,
        spec: Dict[str, Any],
    ) -> List[Tuple[Recipient, NotificationChannel, str]]:
        """Resolve direct address specification."""
        temp_recipient = Recipient(
            id=f"direct-{spec['address']}",
            name="Direct Recipient",
            role=RecipientRole.EXTERNAL,
            contacts=[
                ContactInfo(
                    channel=NotificationChannel(spec["channel"]),
                    address=spec["address"],
                    verified=True,
                )
            ],
        )
        return [
            (
                temp_recipient,
                NotificationChannel(spec["channel"]),
                spec["address"],
            )
        ]

    def _save_to_storage(self) -> None:
        """Save registry data to storage."""
        if not self.storage_path:
            return

        try:
            # Prepare data for serialization
            data = {
                "version": "1.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "recipients": {
                    rid: {
                        "id": r.id,
                        "name": r.name,
                        "role": r.role.value,
                        "contacts": [
                            {
                                "channel": c.channel.value,
                                "address": c.address,
                                "verified": c.verified,
                                "preferred": c.preferred,
                            }
                            for c in r.contacts
                        ],
                        "tags": list(r.tags),
                    }
                    for rid, r in self.recipients.items()
                },
                "escalation_chains": {
                    eid: {
                        "id": e.id,
                        "name": e.name,
                        "description": e.description,
                        "levels": e.levels,
                        "tags": list(e.tags),
                    }
                    for eid, e in self.escalation_chains.items()
                },
                "on_call_schedules": {
                    sid: {
                        "id": s.id,
                        "name": s.name,
                        "description": s.description,
                        "timezone": s.timezone,
                        "enabled": s.enabled,
                        "shifts": [
                            {
                                "recipient_id": shift.recipient_id,
                                "start_time": shift.start_time.isoformat(),
                                "end_time": shift.end_time.isoformat(),
                                "is_primary": shift.is_primary,
                            }
                            for shift in s.shifts
                        ],
                        "tags": list(s.tags),
                    }
                    for sid, s in self.on_call_schedules.items()
                },
                "preferences": {
                    pid: {
                        "recipient_id": p.recipient_id,
                        "channels": {k.value: v for k, v in p.channels.items()},
                        "severity_threshold": p.severity_threshold,
                        "quiet_hours_enabled": p.quiet_hours_enabled,
                        "quiet_hours_start": p.quiet_hours_start.isoformat(),
                        "quiet_hours_end": p.quiet_hours_end.isoformat(),
                        "timezone": p.timezone,
                        "frequency_limits": p.frequency_limits,
                        "excluded_types": list(p.excluded_types),
                        "metadata": p.metadata,
                    }
                    for pid, p in self.preferences.items()
                },
            }

            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info("Registry data saved to %s", self.storage_path)
        except Exception as e:
            logger.error("Failed to save registry data: %s", e)
            raise

    def _load_from_storage(self) -> None:
        """Load registry data from storage."""
        if not self.storage_path:
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load recipients
            for rid, rdata in data.get("recipients", {}).items():
                contacts = [
                    ContactInfo(
                        channel=NotificationChannel(c["channel"]),
                        address=c["address"],
                        verified=c.get("verified", False),
                        preferred=c.get("preferred", False),
                    )
                    for c in rdata.get("contacts", [])
                ]

                recipient = Recipient(
                    id=rdata["id"],
                    name=rdata["name"],
                    role=RecipientRole(rdata["role"]),
                    contacts=contacts,
                    tags=set(rdata.get("tags", [])),
                )
                self.recipients[rid] = recipient

            # Load escalation chains
            for eid, edata in data.get("escalation_chains", {}).items():
                chain = EscalationChain(
                    id=edata["id"],
                    name=edata["name"],
                    description=edata.get("description", ""),
                    levels=edata.get("levels", []),
                    tags=set(edata.get("tags", [])),
                )
                self.escalation_chains[eid] = chain

            # Load on-call schedules
            for sid, sdata in data.get("on_call_schedules", {}).items():
                schedule = OnCallSchedule(
                    id=sdata["id"],
                    name=sdata["name"],
                    description=sdata.get("description", ""),
                    shifts=sdata.get("shifts", []),
                    timezone=sdata.get("timezone", "UTC"),
                )
                self.on_call_schedules[sid] = schedule

            # Load preferences
            for pid, pdata in data.get("preferences", {}).items():
                preferences = NotificationPreferences(
                    recipient_id=pdata["recipient_id"],
                    timezone=pdata.get("timezone", "UTC"),
                )
                self.preferences[pid] = preferences

            logger.info("Registry data loaded from %s", self.storage_path)
            logger.info(
                "Loaded %d recipients, %d escalation chains, %d schedules",
                len(self.recipients),
                len(self.escalation_chains),
                len(self.on_call_schedules),
            )

        except FileNotFoundError:
            logger.warning(
                "Storage file not found at %s, initializing defaults", self.storage_path
            )
            self._initialize_defaults()
        except (ValueError, KeyError, IOError) as e:
            logger.error("Failed to load registry data: %s", e)
            logger.warning("Initializing with defaults")
            self._initialize_defaults()
