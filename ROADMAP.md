# Zero Trust AI Agent Mesh: Feature & Security Roadmap

This document serves as the master blueprint for the Zero Trust AI Agent Mesh. It tracks advanced security, observability, and infrastructure features to be implemented across the project's lifecycle.

---

## 🟢 Category: Observability & Resilience (The "Reliable Mesh")
*Focus: Traceability, health monitoring, and error handling.*

- [ ] **Correlation IDs**: Implement a unique `X-Correlation-ID` generated at the Frontend and propagated through all agent hops (Researcher → Writer) for distributed tracing.
- [ ] **Structured Identity Logging**: Standardize JSON logs in the `AgentServer` to include validated **Caller SPIFFE ID**, **User ID**, and request metadata.
- [ ] **mTLS Forensics**: Log peer certificate serial numbers and SVID expiration dates during the TLS handshake to aid in security audits.
- [ ] **Comprehensive Health Checks**: Expand the `/health` endpoint to include SPIRE socket status and external API connectivity (Gemini/Tavily).
- [ ] **Reliability Patterns**: Implement exponential backoff retries and circuit breakers for all inter-agent and external API communication.

## 🛡️ Category: Advanced Security (The "Defense in Depth")
*Focus: Cryptographic hardening and secret management.*

- [ ] **Secret-less API Access**: Integrate with a Secret Provider (e.g., HashiCorp Vault) using SPIFFE Auth to retrieve short-lived API keys, eliminating static `.env` secrets.
- [ ] **Cryptographic Response Signing**: Use the Agent's SVID private key to sign AI-generated content (JWS). The Frontend validates the signature to ensure content integrity.
- [ ] **Egress Filtering / Domain Pinning**: Use a SPIFFE-aware proxy (like Envoy) to restrict agents' outbound traffic strictly to approved API domains.
- [ ] **User-Contextual Authorization**: Propagate a scoped User JWT. Agents validate that the calling service (e.g., Researcher) has delegated authority for that specific human user.
- [ ] **Automated Data Guardrails**: Implement a security interceptor to scan prompts and responses for PII (Personally Identifiable Information) or accidental secret leakage.

## 📜 Category: Policy & Governance (The "Rules of Engagement")
*Focus: Flexible authorization and identity bridging.*

- [ ] **Policy-as-Code (OPA)**: Replace hardcoded `ALLOWED_CALLERS` with **Open Policy Agent (OPA)** for dynamic, centralized authorization logic.
- [ ] **Dynamic Capability Scoping**: Restrict specific agent functions (e.g., "Deep Search" vs "Fast Search") based on the caller's verified SPIFFE ID or user role.
- [ ] **Human-to-Machine Bridge**: Tighten the binding between the human's OAuth session and the service's SPIFFE identity for end-to-end provenance.

## 🏗️ Category: Production Infrastructure
*Focus: Deployment, scale, and lifecycle management.*

- [ ] **Kubernetes Native Deployment**: Migrate from Docker Compose to K8s using the SPIRE CSI driver for native identity injection.
- [ ] **Automated Registration**: Implement a controller to auto-register workloads in SPIRE based on repository metadata or container labels.
- [ ] **SVID Lifecycle Management**: Tune SVID TTLs and rotation intervals for high-security, low-latency environments.

---

## 📈 Implementation Status Tracker

| Feature | Category | Status | Target Phase | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **mTLS Handshake** | Security | ✅ Done | Phase 1 | Foundation for all A2A. |
| **A2A Authorization** | Policy | ✅ Done | Phase 2 | Basic SPIFFE ID validation. |
| **Gemini REST API** | Workflow | ✅ Done | Phase 2 | Bypassed SDK 404 issues. |
| **Correlation IDs** | Observability | ⏳ Next | Phase 3 | |
| **Secret-less Vault Access** | Security | 📅 Planned | Phase 3 | |
| **Response Signing** | Security | 📅 Planned | Phase 4 | |

---
*Last Updated: 2026-01-26*
