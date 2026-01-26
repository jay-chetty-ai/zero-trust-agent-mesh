# Phase 1: Identity & Authentication - Issues and Fixes

## 1. SPIRE Socket Access Denied
- **Issue**: Agent services (Frontend, Researcher, Writer) were unable to connect to the SPIRE Workload API at `unix:///run/spire/sockets/agent.sock`.
- **Root Cause**: The Unix socket volume was not correctly shared between the `spire-agent` container and the AI workload containers in `docker-compose.yaml`.
- **Fix**: Verified and ensured the `shared-sockets` volume was correctly mounted to `/run/spire/sockets` in all service definitions.

## 2. Docker Build Dependency Mismatches
- **Issue**: Initial builds of the `Dockerfile.agent` failed due to missing system libraries or Python packages (e.g., `aiohttp`, `pyspiffe`).
- **Fix**: Updated `requirements.txt` and optimized the `Dockerfile.agent` to use a consistent `python:3.11-slim` base image with the necessary build-essential tools.

## 3. Mock OAuth Integration
- **Issue**: The Streamlit frontend required a "Login with Google" flow which isn't easy to simulate in a local, non-public environment.
- **Fix**: Implemented a Mock OAuth handler that simulates the login process, allowing the system to populate `st.session_state.user_info` for identity propagation without needing real Google API credentials.

## 4. SVID Retrieval Delays
- **Issue**: On startup, agents would occasionally fail because the `spire-agent` hadn't fully issued the SVID yet.
- **Fix**: Implemented a retry/wait logic in the `SpiffeHelper` to ensure the agent blocks (or retries) until the SVID is successfully fetched from the Workload API.

## 5. Metadata Propagation
- **Issue**: User metadata (e.g., `user_id`) was not being correctly passed from the Frontend to the agents.
- **Fix**: Standardized the JSON payload structure across all agent calls, ensuring `user_id` and `query` are always present in the POST request body.
