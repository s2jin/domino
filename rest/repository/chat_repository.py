from database.interface import session_scope
from database.models.chat import ChatSession, ChatMessage


class ChatRepository:
    def create_session(self, chat_session: ChatSession) -> ChatSession:
        with session_scope() as session:
            session.add(chat_session)
            session.flush()
            session.refresh(chat_session)
            session.expunge(chat_session)
        return chat_session

    def list_sessions(self, user_id: int) -> list:
        with session_scope() as session:
            results = (
                session.query(ChatSession)
                .filter(ChatSession.user_id == user_id)
                .order_by(ChatSession.updated_at.desc())
                .all()
            )
            session.expunge_all()
        return results

    def get_session(self, session_id: int, user_id: int) -> ChatSession:
        with session_scope() as session:
            result = (
                session.query(ChatSession)
                .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
                .first()
            )
            if result:
                session.expunge(result)
        return result

    def delete_session(self, session_id: int, user_id: int) -> bool:
        with session_scope() as session:
            chat = (
                session.query(ChatSession)
                .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
                .first()
            )
            if not chat:
                return False
            session.delete(chat)
            session.flush()
        return True

    def update_session_title(self, session_id: int, user_id: int, title: str) -> ChatSession:
        with session_scope() as session:
            chat = (
                session.query(ChatSession)
                .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
                .first()
            )
            if not chat:
                return None
            chat.title = title
            session.flush()
            session.refresh(chat)
            session.expunge(chat)
        return chat

    def add_message(self, message: ChatMessage) -> ChatMessage:
        with session_scope() as session:
            session.add(message)
            session.flush()
            session.refresh(message)
            session.expunge(message)
        return message

    def get_messages(self, session_id: int, user_id: int) -> list:
        with session_scope() as session:
            chat = (
                session.query(ChatSession)
                .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
                .first()
            )
            if not chat:
                return None
            results = (
                session.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            session.expunge_all()
        return results
