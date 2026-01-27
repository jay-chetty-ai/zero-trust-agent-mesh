# Setup Guide

## Prerequisites

*   **OS**: Linux (Ubuntu recommended)
*   **Docker Engine**: 20.10+
*   **Docker Compose**: V2+
*   **Git**

## Configuration

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repo-url>
    cd spiffe-spire-demo
    ```

2.  **Environment Variables**:
    Create a `.env` file in the root directory:
    ```bash
    touch .env
    ```
    
    Edit `.env` to add your keys:
    ```ini
    # Gemini API Key (Required for Writer Agent)
    GOOGLE_API_KEY=AIza...
    
    # Tavily API Key (Required for Researcher Agent)
    TAVILY_API_KEY=tvly-...
    ```

## Running the Infrastructure

1.  **Start SPIRE and Agents**:
    We use Docker Compose to bring up the entire mesh.
    ```bash
    docker-compose up -d
    ```

2.  **Bootstrap Trust (Registration)**:
    SPIRE Server needs to know which containers are authorized to get which identities. Run the registration script inside the server container:
    ```bash
    docker-compose exec spire-server sh /run/spire/registration/entries.sh
    # OR if running from host with updated script:
    # bash conf/registration/entries.sh
    ```
    *This script creates registration entries mapping Docker labels (like `com.docker.compose.service=researcher`) to SPIFFE IDs.*

3.  **Verify Status**:
    Check if agents have received their SVIDs.
    ```bash
    docker-compose logs -f researcher
    ```
    You should see logs indicating "SVID Updated" or "Success: AgentServer 'researcher' is running".

## Usage

1.  Open your browser to `http://localhost:8501` (Frontend UI).
2.  Click "Login" (Mock Login) to authenticate.
3.  Enter a query (e.g., "AI Agent Mesh with SPIFFE") and click "Research & Write".
4.  The Workflow:
    *   **Frontend** securely calls **Researcher Agent** (mTLS).
    *   **Researcher Agent** uses Tavily to search and calls **Writer Agent** (mTLS).
    *   **Writer Agent** generates content via Gemini API and returns it to Researcher.
    *   **Researcher** returns final result to **Frontend**.

## Troubleshooting

*   **SVID errors**: Ensure the `entries.sh` script ran successfully.
*   **Connection refused**: Check if the `shared-sockets` volume is correctly mounted in `docker-compose.yaml`.
*   **403 Forbidden**: Check if the `ALLOWED_CALLERS` in the agent code includes the caller's SPIFFE ID.
