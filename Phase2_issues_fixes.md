# Phase 2: AI Workflow & A2A Security - Issues and Fixes

## 1. Intermittent "404 Not Found" Errors
- **Issue**: Requests from the Frontend to the Researcher agent were hitting the server but returning 404, even though the handler was defined.
- **Root Cause**: In the `AgentServer` wrapper, the `aiohttp` routes were being registered (`add_routes`) before the decorators in the agent files had a chance to populate the `RouteTableDef`.
- **Fix**: Moved the `self.app.add_routes(self.routes)` call into the `run()` method of the `AgentServer` to ensure it happens after all handlers are defined.

## 2. Gemini SDK Failures
- **Issue**: Both `langchain-google-genai` and the official `google-generativeai` SDKs consistently returned `404 Not Found` when trying to call Gemini models (e.g., `gemini-1.5-flash`).
- **Root Cause**: Unknown internal library/environment conflict in the slim Docker containers that prevented the SDKs from correctly resolving the v1beta endpoints.
- **Fix**: Replaced the SDKs with a **direct REST API call** using `aiohttp`. This followed the user's working `curl` example and bypassed the abstraction layers of the SDK entirely.

## 3. Routing Metadata Loss
- **Issue**: The `aiohttp` router was losing track of function names and handlers when multiple decorators were stacked.
- **Fix**: Applied `@functools.wraps(handler)` to the `require_identity` decorator in `src/common/server.py` to preserve function signatures and metadata, ensuring the router matches paths correctly.

## 4. Model Versioning Confusion
- **Issue**: Initial attempts used `gemini-pro`, which was deprecated or unavailable in certain regions/versions of the v1beta API.
- **Fix**: Standardized the model to `gemini-2.0-flash` after verifying it was supported via a `list_models()` diagnostic check.

## 5. Agent-to-Agent Authorization (A2A)
- **Issue**: The Writer agent initially rejected calls from the Researcher agent despite the mTLS connection being established.
- **Root Cause**: The authorization policy (the "Allowed SPIFFE IDs" list) in the Writer agent did not yet include the Researcher's identity.
- **Fix**: Updated the `ALLOWED_CALLERS` list in `src/agents/writer.py` to include `spiffe://example.org/ns/agents/sa/researcher`, enabling the full Zero Trust mesh communication.
