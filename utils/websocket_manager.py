"""
WebSocket Manager for Real-Time Collaboration
Enables real-time updates and multi-user collaboration
"""
import logging
import asyncio
import json
from typing import Dict, Set, Any, Optional, Callable
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class CollaborationSession:
    """Represents a collaboration session"""
    
    def __init__(self, session_id: str, owner: str):
        self.session_id = session_id
        self.owner = owner
        self.participants: Set[str] = {owner}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.shared_state: Dict[str, Any] = {}
        self.message_history: list = []
    
    def add_participant(self, user_id: str):
        """Add participant to session"""
        self.participants.add(user_id)
        self.last_activity = datetime.now()
    
    def remove_participant(self, user_id: str):
        """Remove participant from session"""
        self.participants.discard(user_id)
        self.last_activity = datetime.now()
    
    def update_state(self, key: str, value: Any):
        """Update shared state"""
        self.shared_state[key] = value
        self.last_activity = datetime.now()
    
    def add_message(self, user_id: str, message: str, message_type: str = "chat"):
        """Add message to history"""
        msg = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "message": message,
            "type": message_type,
            "timestamp": datetime.now().isoformat()
        }
        self.message_history.append(msg)
        self.last_activity = datetime.now()
        return msg
    
    def get_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "owner": self.owner,
            "participants": list(self.participants),
            "participant_count": len(self.participants),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": len(self.message_history)
        }

class WebSocketConnection:
    """Represents a WebSocket connection"""
    
    def __init__(self, connection_id: str, user_id: str):
        self.connection_id = connection_id
        self.user_id = user_id
        self.session_id: Optional[str] = None
        self.connected_at = datetime.now()
        self.last_ping = datetime.now()
        self.message_queue: asyncio.Queue = asyncio.Queue()
    
    async def send_message(self, message: Dict[str, Any]):
        """Queue message for sending"""
        await self.message_queue.put(message)
    
    async def get_message(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Get next message from queue"""
        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    
    def update_ping(self):
        """Update last ping time"""
        self.last_ping = datetime.now()
    
    def is_alive(self, timeout: int = 60) -> bool:
        """Check if connection is alive"""
        elapsed = (datetime.now() - self.last_ping).total_seconds()
        return elapsed < timeout

class WebSocketManager:
    """
    Manages WebSocket connections and collaboration sessions
    """
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.sessions: Dict[str, CollaborationSession] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the WebSocket manager"""
        logger.info("Starting WebSocket manager")
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the WebSocket manager"""
        logger.info("Stopping WebSocket manager")
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """Periodically cleanup dead connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._cleanup_dead_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_dead_connections(self):
        """Remove dead connections"""
        dead_connections = [
            conn_id for conn_id, conn in self.connections.items()
            if not conn.is_alive()
        ]
        
        for conn_id in dead_connections:
            await self.disconnect(conn_id)
        
        if dead_connections:
            logger.info(f"Cleaned up {len(dead_connections)} dead connections")
    
    async def connect(self, user_id: str) -> str:
        """
        Create new WebSocket connection
        
        Returns:
            connection_id
        """
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(connection_id, user_id)
        
        self.connections[connection_id] = connection
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        logger.info(f"User {user_id} connected with connection {connection_id}")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a connection"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        user_id = connection.user_id
        
        # Leave session if in one
        if connection.session_id:
            await self.leave_session(connection_id)
        
        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove connection
        del self.connections[connection_id]
        logger.info(f"Connection {connection_id} disconnected")
    
    async def create_session(self, connection_id: str) -> str:
        """
        Create new collaboration session
        
        Returns:
            session_id
        """
        if connection_id not in self.connections:
            raise ValueError("Invalid connection")
        
        connection = self.connections[connection_id]
        session_id = str(uuid.uuid4())
        
        session = CollaborationSession(session_id, connection.user_id)
        self.sessions[session_id] = session
        
        connection.session_id = session_id
        
        logger.info(f"Session {session_id} created by {connection.user_id}")
        return session_id
    
    async def join_session(self, connection_id: str, session_id: str):
        """Join existing collaboration session"""
        if connection_id not in self.connections:
            raise ValueError("Invalid connection")
        
        if session_id not in self.sessions:
            raise ValueError("Invalid session")
        
        connection = self.connections[connection_id]
        session = self.sessions[session_id]
        
        # Leave current session if in one
        if connection.session_id:
            await self.leave_session(connection_id)
        
        # Join new session
        connection.session_id = session_id
        session.add_participant(connection.user_id)
        
        # Notify other participants
        await self._broadcast_to_session(
            session_id,
            {
                "type": "user_joined",
                "user_id": connection.user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            },
            exclude_connection=connection_id
        )
        
        logger.info(f"User {connection.user_id} joined session {session_id}")
    
    async def leave_session(self, connection_id: str):
        """Leave current collaboration session"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        if not connection.session_id:
            return
        
        session_id = connection.session_id
        if session_id not in self.sessions:
            connection.session_id = None
            return
        
        session = self.sessions[session_id]
        session.remove_participant(connection.user_id)
        
        # Notify other participants
        await self._broadcast_to_session(
            session_id,
            {
                "type": "user_left",
                "user_id": connection.user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            },
            exclude_connection=connection_id
        )
        
        connection.session_id = None
        
        # Delete session if empty
        if not session.participants:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} deleted (no participants)")
        
        logger.info(f"User {connection.user_id} left session {session_id}")
    
    async def send_message(
        self,
        connection_id: str,
        message: str,
        message_type: str = "chat"
    ):
        """Send message to session"""
        if connection_id not in self.connections:
            raise ValueError("Invalid connection")
        
        connection = self.connections[connection_id]
        if not connection.session_id:
            raise ValueError("Not in a session")
        
        session_id = connection.session_id
        if session_id not in self.sessions:
            raise ValueError("Invalid session")
        
        session = self.sessions[session_id]
        msg = session.add_message(connection.user_id, message, message_type)
        
        # Broadcast to all participants
        await self._broadcast_to_session(
            session_id,
            {
                "type": "message",
                "message": msg,
                "session_id": session_id
            }
        )
    
    async def update_shared_state(
        self,
        connection_id: str,
        key: str,
        value: Any
    ):
        """Update shared state in session"""
        if connection_id not in self.connections:
            raise ValueError("Invalid connection")
        
        connection = self.connections[connection_id]
        if not connection.session_id:
            raise ValueError("Not in a session")
        
        session_id = connection.session_id
        if session_id not in self.sessions:
            raise ValueError("Invalid session")
        
        session = self.sessions[session_id]
        session.update_state(key, value)
        
        # Broadcast state update
        await self._broadcast_to_session(
            session_id,
            {
                "type": "state_update",
                "key": key,
                "value": value,
                "user_id": connection.user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def _broadcast_to_session(
        self,
        session_id: str,
        message: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ):
        """Broadcast message to all session participants"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        # Find all connections in session
        session_connections = [
            conn for conn in self.connections.values()
            if conn.session_id == session_id
            and conn.connection_id != exclude_connection
        ]
        
        # Send to all connections
        tasks = [conn.send_message(message) for conn in session_connections]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def ping(self, connection_id: str):
        """Update connection ping time"""
        if connection_id in self.connections:
            self.connections[connection_id].update_ping()
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if session_id not in self.sessions:
            return None
        return self.sessions[session_id].get_info()
    
    def get_active_sessions(self) -> list[Dict[str, Any]]:
        """Get all active sessions"""
        return [session.get_info() for session in self.sessions.values()]
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information"""
        if connection_id not in self.connections:
            return None
        
        conn = self.connections[connection_id]
        return {
            "connection_id": conn.connection_id,
            "user_id": conn.user_id,
            "session_id": conn.session_id,
            "connected_at": conn.connected_at.isoformat(),
            "last_ping": conn.last_ping.isoformat(),
            "is_alive": conn.is_alive()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        return {
            "total_connections": len(self.connections),
            "total_sessions": len(self.sessions),
            "total_users": len(self.user_connections),
            "active_connections": sum(1 for conn in self.connections.values() if conn.is_alive())
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

# Made with Bob