import streamlit as st
import asyncio
import aiohttp
import ssl
import logging
from src.common.spiffe import SpiffeHelper

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("frontend")

# --- Page Config ---
st.set_page_config(page_title="Secure AI Agents", page_icon="🛡️")

# --- SPIFFE Initialization (Cached) ---
@st.cache_resource
def get_spiffe_helper():
    helper = SpiffeHelper()
    helper.start() # Blocks until SVID is ready
    return helper

try:
    spiffe = get_spiffe_helper()
    logger.info("Frontend: SPIFFE SVID Ready.")
except Exception as e:
    st.error(f"Failed to initialize SPIFFE Identity: {e}")
    st.stop()

# --- OAuth Logic (Mock) ---
if "user_token" not in st.session_state:
    st.session_state.user_token = None
    st.session_state.user_info = None

def login():
    # Simulate OAuth Redirect & Callback
    st.session_state.user_token = "mock_jwt_token_123"
    st.session_state.user_info = {"email": "alice@example.org", "id": "user_alice"}
    st.rerun() # Refresh to show logged-in state

def logout():
    st.session_state.user_token = None
    st.session_state.user_info = None
    st.rerun()

# --- Helper to Call Agents ---
async def call_agent(agent_host, endpoint, payload):
    url = f"https://{agent_host}:8080{endpoint}"
    
    # Get Client SSL Context (with my SVID)
    ssl_context = spiffe.get_client_ssl_context()
    
    # Strict A2A Logic
    # We must trust that DNS/Host resolves, BUT verification is done via SVID (SAN-URI), NOT Hostname.
    # aiohttp default checks hostname. We disabled it in get_client_ssl_context (check_hostname=False).
    # But we still need to pass scope.
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, ssl=ssl_context) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"status": "error", "code": resp.status, "text": await resp.text()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- UI Layout ---
st.title("🛡️ Zero Trust AI Agent Mesh")

if not st.session_state.user_token:
    st.warning("Please authenticate (OAuth) to access the System.")
    if st.button("Login with Google (Mock)"):
        login()
else:
    user = st.session_state.user_info
    st.sidebar.success(f"Logged in as: {user['email']}")
    if st.sidebar.button("Logout"):
        logout()
        
    st.markdown("### Research Assistant")
    
    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask me anything..."):
        # User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Agent Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.text("Authenticating & contacting Mesh...")
            
            # Prepare Payload with Identity Propagation
            payload = {
                "query": prompt,
                "user_id": user['id']
            }
            
            # Run Async Call in Sync Streamlit
            response = asyncio.run(call_agent("researcher", "/ask", payload))
            
            if response.get("status") == "success":
                answer = response.get("answer")
                verified_by = response.get("verified_caller")
                
                full_reply = f"{answer}\n\n*🔒 Verified Secure Connection from: {verified_by}*"
                message_placeholder.markdown(full_reply)
                st.session_state.messages.append({"role": "assistant", "content": full_reply})
            else:
                err_msg = f"❌ Agent Interaction Failed: {response}"
                message_placeholder.error(err_msg)
