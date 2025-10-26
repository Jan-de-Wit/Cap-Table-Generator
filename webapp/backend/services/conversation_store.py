"""
Conversation Store - Manages conversation history and context.
Handles conversation state, message history, and cleanup.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class ConversationStore:
    """
    Manages conversation state in-memory.
    Tracks message history per conversation ID.
    """
    
    def __init__(self, ttl_hours: int = 24):
        """
        Initialize conversation store.
        
        Args:
            ttl_hours: Time to live for conversations in hours
        """
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.ttl_hours = ttl_hours
        self.lock = Lock()
        
        logger.info(f"ConversationStore initialized with TTL={ttl_hours} hours")
    
    def create_conversation(self, initial_messages: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Create a new conversation.
        
        Args:
            initial_messages: Optional initial messages to add
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        
        conversation = {
            "id": conversation_id,
            "messages": initial_messages or [],
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
        }
        
        with self.lock:
            self.conversations[conversation_id] = conversation
        
        logger.info(f"Created new conversation: {conversation_id}")
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation by ID.
        Updates last_accessed timestamp.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation data or None if not found
        """
        with self.lock:
            conversation = self.conversations.get(conversation_id)
            
            if conversation:
                conversation["last_accessed"] = datetime.now()
                return conversation
            
            return None
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Get all messages for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            List of messages
        """
        conversation = self.get_conversation(conversation_id)
        if conversation:
            return conversation.get("messages", [])
        return []
    
    def add_messages(self, conversation_id: str, messages: List[Dict[str, str]]) -> bool:
        """
        Add messages to a conversation.
        
        Args:
            conversation_id: Conversation identifier
            messages: Messages to add
            
        Returns:
            True if added, False if conversation doesn't exist
        """
        with self.lock:
            conversation = self.conversations.get(conversation_id)
            
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return False
            
            conversation["messages"].extend(messages)
            conversation["last_accessed"] = datetime.now()
            
            logger.debug(f"Added {len(messages)} messages to conversation {conversation_id}")
            return True
    
    def update_messages(self, conversation_id: str, messages: List[Dict[str, str]]) -> bool:
        """
        Replace all messages for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            messages: New messages list
            
        Returns:
            True if updated, False if conversation doesn't exist
        """
        with self.lock:
            conversation = self.conversations.get(conversation_id)
            
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return False
            
            conversation["messages"] = messages
            conversation["last_accessed"] = datetime.now()
            
            logger.debug(f"Updated conversation {conversation_id} with {len(messages)} messages")
            return True
    
    def cleanup_expired(self) -> int:
        """
        Remove expired conversations.
        
        Returns:
            Number of conversations removed
        """
        now = datetime.now()
        ttl = timedelta(hours=self.ttl_hours)
        
        to_remove = []
        
        with self.lock:
            for conversation_id, conversation in self.conversations.items():
                age = now - conversation["last_accessed"]
                if age > ttl:
                    to_remove.append(conversation_id)
            
            for conversation_id in to_remove:
                del self.conversations[conversation_id]
                logger.info(f"Removed expired conversation: {conversation_id}")
        
        return len(to_remove)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                logger.info(f"Deleted conversation: {conversation_id}")
                return True
            
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get store statistics.
        
        Returns:
            Dictionary with stats
        """
        with self.lock:
            now = datetime.now()
            oldest = None
            newest = None
            
            for conversation in self.conversations.values():
                accessed = conversation["last_accessed"]
                if oldest is None or accessed < oldest:
                    oldest = accessed
                if newest is None or accessed > newest:
                    newest = accessed
            
            return {
                "total_conversations": len(self.conversations),
                "ttl_hours": self.ttl_hours,
                "oldest_conversation": oldest.isoformat() if oldest else None,
                "newest_conversation": newest.isoformat() if newest else None,
            }
    
    def list_conversations(self) -> List[str]:
        """
        List all conversation IDs.
        
        Returns:
            List of conversation IDs
        """
        with self.lock:
            return list(self.conversations.keys())


# Global store instance
conversation_store = ConversationStore(ttl_hours=24)

