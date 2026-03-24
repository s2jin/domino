"""Dummy LLM Agent Service.

Streams doing/tool/done events as newline-delimited JSON.
Replace the logic inside `chat()` with real LLM agent calls.
"""
import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="LLM Agent Service")


class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]


@app.post("/chat")
async def chat(request: ChatRequest):
    messages = request.messages

    # Get the last user message
    user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break

    async def generate():
        # Step 1: Think
        yield json.dumps({"type": "doing", "content": "Analyzing your message..."}) + "\n"
        await asyncio.sleep(0.5)

        # Step 2: Tool call
        yield json.dumps({
            "type": "tool",
            "content": json.dumps({
                "name": "search",
                "args": {"query": user_message},
                "result": f"Found 3 results for '{user_message}'"
            })
        }) + "\n"
        await asyncio.sleep(0.5)

        # Step 3: Think again
        yield json.dumps({"type": "doing", "content": "Generating response..."}) + "\n"
        await asyncio.sleep(0.5)

        # Step 4: Done
        yield json.dumps({
            "type": "done",
            "content": f"Based on my search, here is the answer to: {user_message}\n\n[This is a dummy response from the LLM agent]"
        }) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)
