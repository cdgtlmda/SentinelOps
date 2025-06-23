"""
Message handler for communication agent
"""

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime


class MessageHandler:
    """Handles message queuing and delivery"""

    def __init__(self) -> None:
        """Initialize message handler"""
        self.message_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.retry_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self.delivery_status: Dict[str, Dict[str, Any]] = {}

    async def queue_message(self, message: Dict[str, Any]) -> str:
        """Queue a message for delivery"""
        message_id = f"msg_{datetime.now().timestamp()}"
        message['id'] = message_id
        message['queued_at'] = datetime.now().isoformat()
        message['attempts'] = 0

        await self.message_queue.put(message)
        self.delivery_status[message_id] = {
            'status': 'queued',
            'attempts': 0,
            'queued_at': message['queued_at']
        }

        return message_id

    async def get_next_message(self) -> Optional[Dict[str, Any]]:
        """Get next message from queue"""
        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    def update_status(self, message_id: str, status: str, error: Optional[str] = None) -> None:
        """Update message delivery status"""
        if message_id in self.delivery_status:
            self.delivery_status[message_id]['status'] = status
            self.delivery_status[message_id]['last_update'] = datetime.now().isoformat()
            if error:
                self.delivery_status[message_id]['error'] = error
