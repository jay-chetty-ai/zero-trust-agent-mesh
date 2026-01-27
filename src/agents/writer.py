import logging
import aiohttp
from aiohttp import web
from src.common.server import AgentServer

logger = logging.getLogger("writer-agent")

import os

# ... (Logging setup same)

ALLOWED_CALLERS = [
    "spiffe://example.org/ns/ui/sa/frontend",
    "spiffe://example.org/ns/agents/sa/researcher" # Authorized for Phase 2
]

server = AgentServer("writer", port=8080)

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

if GEMINI_API_KEY:
    logger.info(f"Google API Key found (starts with: {GEMINI_API_KEY[:8]}...)")
else:
    logger.error("GOOGLE_API_KEY NOT FOUND in environment!")

@server.routes.post('/process')
@server.require_user_context(allowed_callers=ALLOWED_CALLERS)
async def process_content(request):
    data = await request.json()
    content = data.get('content')
    caller_id = request.get('caller_id')
    user_context = request.get('user_context')
    user_id = user_context.get('sub')
    
    logger.info(f"Writer Request from {caller_id} for User {user_id}")
    
    if not GEMINI_API_KEY:
         return web.json_response({"status": "error", "message": "Writer API Key not configured."})
         
    try:
        # Prompt Engineering
        prompt_text = f"""You are an expert technical writer. 
        Based on the following research notes, write a concise, engaging blog post.
        
        Notes:
        {content}
        
        Format: Markdown.
        """
        
        # Prepare Payload for Gemini (as per user's working curl)
        gemini_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text}
                    ]
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        }
        
        logger.info("Invoking Gemini Writer via Direct REST API...")
        async with aiohttp.ClientSession() as session:
            async with session.post(GEMINI_URL, json=gemini_payload, headers=headers) as resp:
                if resp.status == 200:
                    resp_json = await resp.json()
                    # Extract text from response candidate
                    try:
                        article = resp_json['candidates'][0]['content']['parts'][0]['text']
                        logger.info("Writing Complete.")
                        return web.json_response(server.sign_response({
                            "result": article
                        }))
                    except (KeyError, IndexError) as e:
                        logger.error(f"Malformed Gemini response: {resp_json}")
                        return web.json_response({"status": "error", "message": "Refused to generate or malformed response"})
                else:
                    err_text = await resp.text()
                    logger.error(f"Gemini API Error {resp.status}: {err_text}")
                    return web.json_response({"status": "error", "message": f"Gemini API Error: {resp.status}"}, status=resp.status)
        
    except Exception as e:
        logger.error(f"Writing failed: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)



if __name__ == "__main__":
    server.run()
