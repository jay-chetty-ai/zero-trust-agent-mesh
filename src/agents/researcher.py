import logging
import sys
import aiohttp
from aiohttp import web
from src.common.server import AgentServer

# Configure Logging
logging.basicConfig(level=logging.INFO)
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
@server.require_identity(allowed_ids=ALLOWED_CALLERS)
async def ask_agent(request):
    data = await request.json()
    query = data.get('query')
    user_id = data.get('user_id', 'unknown')
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
        
        # Identity Propagation: We use OUR SVID (researcher) to call Writer.
        # Writer must authorize US.
        
        # Get Client SSL Context
        ssl_context = server.spiffe.get_client_ssl_context()
        
        logger.info(f"Calling Writer Agent at {writer_url}...")
        async with aiohttp.ClientSession() as session:
            async with session.post(writer_url, json=writer_payload, ssl=ssl_context) as resp:
                if resp.status == 200:
                    writer_resp = await resp.json()
                    final_article = writer_resp.get("result")
                    verified_writer = "spiffe://example.org/ns/agents/sa/writer" # Implicit trust if connection worked? 
                    # Ideally we validate the server cert too if we want strict mutual authn check in app logic
                    # but pyspiffe context handles validation.
                else:
                    error_text = await resp.text()
                    logger.error(f"Writer call failed: {resp.status} - {error_text}")
                    final_article = f"Error generating article. Search results: {search_results[:200]}..."

        return web.json_response({
            "status": "success",
            "answer": final_article,
            "verified_caller": caller_id # To show frontend we accepted them
        })
        
    except Exception as e:
        logger.error(f"Error during research: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)



if __name__ == "__main__":
    server.run()
