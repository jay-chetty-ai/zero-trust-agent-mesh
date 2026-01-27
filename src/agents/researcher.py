import logging
import sys
import aiohttp
from aiohttp import web
from src.common.server import AgentServer

# Configure Logging
logger = logging.getLogger("researcher-agent")

import os 
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage

# ... (Logging setup same)

# Define Allowed Callers (Authorization Policy)
ALLOWED_CALLERS = [
    "spiffe://example.org/ns/ui/sa/frontend"
]

server = AgentServer("researcher", port=8080)
# Initialize Tavily
try:
    search_tool = TavilySearchResults(max_results=3)
except Exception as e:
    logger.error(f"Failed Tavily init: {e}")
    search_tool = None

@server.routes.post('/ask')
@server.require_user_context(allowed_callers=ALLOWED_CALLERS)
async def ask_agent(request):
    data = await request.json()
    query = data.get('query')
    user_context = request.get('user_context')
    user_id = user_context.get('sub')
    caller_id = request.get('caller_id')
    
    logger.info(f"RESEARCH REQUEST | Caller: {caller_id} | User: {user_id} | Query: {query}")
    
    try:
        # 1. Perform Real Search
        logger.info("Executing Tavily Search...")
        if search_tool:
            search_results = search_tool.invoke({"query": query})
        else:
            search_results = "Search tool unavailable."
        logger.info("Search Complete.")
        
        # 2. Call Writer Agent (Agent-to-Agent mTLS)
        # We need to act as a Client now.
        writer_url = "https://writer:8080/process"
        
        # Prepare Payload for Writer
        writer_payload = {
            "content": f"Topic: {query}\n\nsearch Results:\n{search_results}",
            "original_user": user_id
        }
        
        # Identity Propagation: We use OUR SVID (researcher) to call Writer,
        # BUT we MUST forward the User's JWT (Bearer token) to satisfy Writer's requirement.
        headers = {
            "Authorization": request.headers.get("Authorization")
        }
        
        # Get Client SSL Context
        ssl_context = server.spiffe.get_client_ssl_context()
        
        logger.info(f"Calling Writer Agent at {writer_url} with User Context...")
        async with aiohttp.ClientSession() as session:
            async with session.post(writer_url, json=writer_payload, ssl=ssl_context, headers=headers) as resp:
                if resp.status == 200:
                    writer_resp = await resp.json()
                    # writer_resp is now { "status": "success", "content": { "result": "..." }, "signature": "..." }
                    final_article = writer_resp.get("content", {}).get("result")
                    writer_signature = writer_resp.get("signature")
                else:
                    error_text = await resp.text()
                    logger.error(f"Writer call failed: {resp.status} - {error_text}")
                    final_article = f"Error generating article. Search results: {search_results[:200]}..."

        return web.json_response(server.sign_response({
            "answer": final_article,
            "writer_signature": writer_signature if 'writer_signature' in locals() else None,
            "verified_caller": caller_id
        }))
        
    except Exception as e:
        logger.error(f"Error during research: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)



if __name__ == "__main__":
    server.run()
