import asyncio
import json
from typing import Dict, List, Set
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends, Request
from fastapi.responses import StreamingResponse
from services.chatbot_service import ChatbotService
from schemas.context.auth_context import AuthorizationContextData
from schemas.requests.chatbot import CreateSessionRequest, UpdateSessionRequest, SendMessageRequest
from schemas.responses.chatbot import (
    ChatSessionResponse,
    ChatSessionDetailResponse,
    ChatMessageResponse,
    SendMessageResponse,
)
from schemas.exceptions.base import BaseException, ResourceNotFoundException
from schemas.errors.base import SomethingWrongError, ResourceNotFoundError
from auth.permission_authorizer import Authorizer

router = APIRouter(prefix="/chatbot")

authorizer = Authorizer()
chatbot_service = ChatbotService()

# In-memory store for SSE: session_id -> list of asyncio.Queue
_sse_subscribers: Dict[int, List[asyncio.Queue]] = {}
# Track cancelled sessions
_cancelled_sessions: Set[int] = set()


@router.post(
    "/sessions",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": ChatSessionResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": SomethingWrongError},
    },
)
def create_session(
    body: CreateSessionRequest,
    auth_context: AuthorizationContextData = Depends(authorizer.auth_wrapper),
) -> ChatSessionResponse:
    try:
        session = chatbot_service.create_session(
            user_id=auth_context.user_id,
            title=body.title or "New Chat",
        )
        return ChatSessionResponse(**session.to_dict())
    except BaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/sessions",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": List[ChatSessionResponse]},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": SomethingWrongError},
    },
)
def list_sessions(
    auth_context: AuthorizationContextData = Depends(authorizer.auth_wrapper),
) -> List[ChatSessionResponse]:
    sessions = chatbot_service.list_sessions(user_id=auth_context.user_id)
    return [ChatSessionResponse(**s.to_dict()) for s in sessions]


@router.get(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": ChatSessionDetailResponse},
        status.HTTP_404_NOT_FOUND: {"model": ResourceNotFoundError},
    },
)
def get_session(
    session_id: int,
    auth_context: AuthorizationContextData = Depends(authorizer.auth_wrapper),
) -> ChatSessionDetailResponse:
    try:
        data = chatbot_service.get_session_with_messages(session_id, auth_context.user_id)
        return ChatSessionDetailResponse(**data)
    except (BaseException, ResourceNotFoundException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    session_id: int,
    auth_context: AuthorizationContextData = Depends(authorizer.auth_wrapper),
):
    try:
        chatbot_service.delete_session(session_id, auth_context.user_id)
    except (BaseException, ResourceNotFoundException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.patch(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": ChatSessionResponse},
        status.HTTP_404_NOT_FOUND: {"model": ResourceNotFoundError},
    },
)
def update_session(
    session_id: int,
    body: UpdateSessionRequest,
    auth_context: AuthorizationContextData = Depends(authorizer.auth_wrapper),
) -> ChatSessionResponse:
    try:
        session = chatbot_service.update_session_title(session_id, auth_context.user_id, body.title)
        return ChatSessionResponse(**session.to_dict())
    except (BaseException, ResourceNotFoundException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/sessions/{session_id}/messages",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": SendMessageResponse},
        status.HTTP_404_NOT_FOUND: {"model": ResourceNotFoundError},
    },
)
def send_message(
    session_id: int,
    body: SendMessageRequest,
    background_tasks: BackgroundTasks,
    auth_context: AuthorizationContextData = Depends(authorizer.auth_wrapper),
) -> SendMessageResponse:
    """Send a user message. Saves user message and triggers async chatbot processing via SSE."""
    try:
        _cancelled_sessions.discard(session_id)
        result = chatbot_service.send_message(session_id, auth_context.user_id, body.content)

        # Call LLM agent service in background
        background_tasks.add_task(
            _call_llm_agent, session_id, auth_context.user_id
        )

        return SendMessageResponse(**result)
    except (BaseException, ResourceNotFoundException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


async def _call_llm_agent(session_id: int, user_id: int):
    """Call LLM agent service and relay streamed events to SSE subscribers."""
    from clients.llm_agent_client import stream_llm_agent

    # Get chat history
    session_data = chatbot_service.get_session_with_messages(session_id, user_id)
    messages = session_data["messages"]

    async for event in stream_llm_agent(messages):
        # Check if cancelled
        if session_id in _cancelled_sessions:
            _cancelled_sessions.discard(session_id)
            return

        event_type = event.get("type", "")
        content = event.get("content", "")

        # Save to DB based on type
        if event_type == "doing" and content:
            chatbot_service.save_think_message(session_id, user_id, content)
        elif event_type == "tool" and content:
            chatbot_service.save_tool_message(session_id, user_id, content)
        elif event_type == "done" and content:
            chatbot_service.save_assistant_message(session_id, user_id, content)

        # Relay to SSE subscribers
        if session_id in _sse_subscribers:
            for q in _sse_subscribers[session_id]:
                await q.put(event)

        # Stop after done or error
        if event_type in ("done", "error"):
            return


@router.post(
    "/sessions/{session_id}/cancel",
    status_code=status.HTTP_200_OK,
)
def cancel_session(
    session_id: int,
    auth_context: AuthorizationContextData = Depends(authorizer.auth_wrapper),
):
    """Cancel an ongoing chatbot operation for this session."""
    _cancelled_sessions.add(session_id)
    # Notify SSE subscribers
    if session_id in _sse_subscribers:
        event = {"type": "cancelled", "content": ""}
        for q in _sse_subscribers[session_id]:
            q.put_nowait(event)
    return {"status": "cancelled"}


@router.get(
    "/sessions/{session_id}/stream",
)
async def stream_session(
    session_id: int,
    request: Request,
    auth_context: AuthorizationContextData = Depends(authorizer.auth_wrapper),
):
    """SSE endpoint for streaming chatbot responses.
    External API can push events via POST /chatbot/sessions/{session_id}/events"""
    queue: asyncio.Queue = asyncio.Queue()

    if session_id not in _sse_subscribers:
        _sse_subscribers[session_id] = []
    _sse_subscribers[session_id].append(queue)

    async def event_generator():
        try:
            # Send connected event immediately so frontend knows SSE is ready
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("type") in ("done", "cancelled", "error"):
                        break
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        finally:
            _sse_subscribers[session_id].remove(queue)
            if not _sse_subscribers[session_id]:
                del _sse_subscribers[session_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/sessions/{session_id}/events",
    status_code=status.HTTP_200_OK,
)
async def push_event(
    session_id: int,
    body: dict,
):
    """Hook endpoint for internal chatbot API to push events.
    Body format:
      {"type": "doing", "content": "Processing step 1..."}
      {"type": "done", "content": "Final answer here"}
      {"type": "error", "content": "Error message"}

    When type is 'done', the content is saved as an assistant message.
    """
    event_type = body.get("type", "doing")
    content = body.get("content", "")

    # Check if session was cancelled
    if session_id in _cancelled_sessions:
        _cancelled_sessions.discard(session_id)
        return {"status": "cancelled"}

    # Find user_id from session
    from database.interface import session_scope
    from database.models.chat import ChatSession as ChatSessionModel
    chat = None
    with session_scope() as db_session:
        chat = db_session.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
        if chat:
            user_id = chat.user_id
            db_session.expunge(chat)

    if chat:
        if event_type == "doing" and content:
            chatbot_service.save_think_message(session_id, user_id, content)
        elif event_type == "done" and content:
            chatbot_service.save_assistant_message(session_id, user_id, content)

    # Push to SSE subscribers
    event = {"type": event_type, "content": content}
    if session_id in _sse_subscribers:
        for q in _sse_subscribers[session_id]:
            await q.put(event)

    return {"status": "ok"}
