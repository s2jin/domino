import json
import httpx
from core.logger import get_configured_logger
from core.settings import settings


logger = get_configured_logger("LLMAgentClient")


async def stream_llm_agent(messages: list[dict]):
    """Call LLM agent service with streaming response.

    Args:
        messages: Chat history in format [{"role": "...", "content": "..."}]

    Yields:
        dict: Events from agent, e.g.:
            {"type": "doing", "content": "Searching..."}
            {"type": "tool", "content": "{\"name\": \"search\", ...}"}
            {"type": "done", "content": "Final answer"}
            {"type": "error", "content": "Error message"}
    """
    url = f"{settings.LLM_AGENT_URL}/chat"

    # Only send role and content to agent (avoid datetime serialization issues)
    clean_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
            async with client.stream("POST", url, json={"messages": clean_messages}) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    logger.error(f"LLM agent returned {response.status_code}: {body[:200]}")
                    yield {"type": "error", "content": f"Agent error: {response.status_code}"}
                    return

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse agent event: {line[:100]}")

    except httpx.ConnectError:
        logger.error(f"Cannot connect to LLM agent at {url}")
        yield {"type": "error", "content": "Cannot connect to LLM agent service"}
    except httpx.ReadTimeout:
        logger.error("LLM agent response timed out")
        yield {"type": "error", "content": "LLM agent timed out"}
    except Exception as e:
        logger.error(f"LLM agent error: {e}")
        yield {"type": "error", "content": f"LLM agent error: {str(e)}"}
