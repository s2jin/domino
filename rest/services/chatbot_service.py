from datetime import datetime
from core.logger import get_configured_logger
from repository.chat_repository import ChatRepository
from database.models.chat import ChatSession, ChatMessage, MessageRole
from schemas.exceptions.base import ResourceNotFoundException


class ChatbotService:
    def __init__(self):
        self.logger = get_configured_logger(self.__class__.__name__)
        self.chat_repository = ChatRepository()

    def create_session(self, user_id: int, title: str = "New Chat") -> ChatSession:
        chat_session = ChatSession(
            title=title,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return self.chat_repository.create_session(chat_session)

    def list_sessions(self, user_id: int) -> list:
        return self.chat_repository.list_sessions(user_id)

    def get_session_with_messages(self, session_id: int, user_id: int) -> dict:
        session = self.chat_repository.get_session(session_id, user_id)
        if not session:
            raise ResourceNotFoundException(message="Chat session not found")
        messages = self.chat_repository.get_messages(session_id, user_id)
        return {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "messages": [
                {
                    "id": m.id,
                    "session_id": m.session_id,
                    "role": m.role.value if hasattr(m.role, 'value') else m.role,
                    "content": m.content,
                    "created_at": m.created_at,
                }
                for m in (messages or [])
            ],
        }

    def delete_session(self, session_id: int, user_id: int):
        deleted = self.chat_repository.delete_session(session_id, user_id)
        if not deleted:
            raise ResourceNotFoundException(message="Chat session not found")

    def update_session_title(self, session_id: int, user_id: int, title: str) -> ChatSession:
        session = self.chat_repository.update_session_title(session_id, user_id, title)
        if not session:
            raise ResourceNotFoundException(message="Chat session not found")
        return session

    def send_message(self, session_id: int, user_id: int, content: str) -> dict:
        """Save user message and call internal chatbot API.
        Returns both user_message and assistant_message."""
        session = self.chat_repository.get_session(session_id, user_id)
        if not session:
            raise ResourceNotFoundException(message="Chat session not found")

        # Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.user,
            content=content,
            created_at=datetime.utcnow(),
        )
        user_msg = self.chat_repository.add_message(user_msg)

        return {
            "user_message": {
                "id": user_msg.id,
                "session_id": user_msg.session_id,
                "role": user_msg.role.value if hasattr(user_msg.role, 'value') else user_msg.role,
                "content": user_msg.content,
                "created_at": user_msg.created_at,
            },
        }

    def save_think_message(self, session_id: int, user_id: int, content: str) -> ChatMessage:
        """Save a think (doing) message."""
        session = self.chat_repository.get_session(session_id, user_id)
        if not session:
            raise ResourceNotFoundException(message="Chat session not found")

        msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.think,
            content=content,
            created_at=datetime.utcnow(),
        )
        return self.chat_repository.add_message(msg)

    def save_assistant_message(self, session_id: int, user_id: int, content: str) -> ChatMessage:
        """Hook for external API to push assistant response."""
        session = self.chat_repository.get_session(session_id, user_id)
        if not session:
            raise ResourceNotFoundException(message="Chat session not found")

        msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.assistant,
            content=content,
            created_at=datetime.utcnow(),
        )
        return self.chat_repository.add_message(msg)
