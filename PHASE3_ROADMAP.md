# Phase 3 Roadmap: Observability, Security & Production Hardening

This document tracks the progress of **Phase 3** for the Zero Trust AI Agent Mesh. The focus is on moving from a functional prototype to a production-ready, observable, and cryptographically hardened system.

---

## 🟢 Monitoring & Observability (The "Audit Trail")
*Goal: Ensure every hop in the mesh is traceable and accountable.*

- [ ] **Correlation IDs**: Implement a `X-Correlation-ID` generated at the Frontend and propagated through all agent calls (Researcher → Writer).
- [ ] **Structured Identity Logging**: Update the `AgentServer` to log every request with the validated **Caller SPIFFE ID** and **User ID** in JSON format.
- [ ] **mTLS Traceability**: Log peer certificate serial numbers and SVID expiration dates during the handshake for security forensics.
- [ ] **Mesh Health Checks**: Expand `/health` to verify SPIRE socket connectivity and external API (Gemini/Tavily) responsiveness.

## 🛡️ Advanced Security (The "Defense in Depth")
*Goal: Remove static secrets and implement content-level trust.*

- [ ] **Secret-less External Access**: Integrate with a Secret Provider (like HashiCorp Vault) using SPIFFE Auth to retrieve short-lived API keys for Gemini/Tavily.
- [ ] **Cryptographic Non-Repudiation**: Use the Agent's SVID private key to sign the AI response (JWS). The Frontend validates the signature to prove the content wasn't modified.
- [ ] **Egress Filtering & Domain Pinning**: Implement network policies or an egress proxy (Envoy) to ensure agents can only talk to approved domains (e.g., `api.tavily.com`).
- [ ] **User-Contextual Authorization**: Pass a scoped User JWT along the chain. Agents validate that the Researcher is authorized to act on behalf of the specific user.
- [ ] **Data Guardrails (PII Scrubbing)**: Implement a security interceptor to scan prompts and responses for accidental leaks of credentials or sensitive data.

## 📜 Policy & Governance (The "Rules of Engagement")
*Goal: Move authorization logic out of the code and into manageable policy.*

- [ ] **Policy-as-Code (OPA)**: Centralize authorization logic using Open Policy Agent (OPA) to evaluate complex rules instead of hardcoded `ALLOWED_CALLERS`.
- [ ] **Dynamic Scoping**: Restrict Agent capabilities (e.g., specific search types or LLM models) based on the caller's identity or user roles.
- [ ] **Human-to-Machine Identity Bridge**: Tighten the link between the Human OAuth context and the Machine SPIFFE context.

## 🏗️ Resilience & Production Hardening
*Goal: Prepare for scale and handle failures gracefully.*

- [ ] **Reliability Patterns**: Implement exponential backoff retries and circuit breakers for all inter-agent and external API calls.
- [ ] **Kubernetes Migration**: Prepare K8s manifests and SPIRE CSI driver configurations for a real-world cluster deployment.
- [ ] **CI/CD Integration**: Automate registration entry creation in SPIRE based on repository/container labels.

---

## 📈 Implementation Progress Tracker

| Feature | Category | Status | Notes |
| :--- | :--- | :--- | :--- |
| **mTLS Handshake** | Security | ✅ Done | Implemented in Phase 1/2 |
| **A2A Authorization** | Policy | ✅ Done | Hardcoded `ALLOWED_CALLERS` |
| **Gemini REST Integration** | Workflow | ✅ Done | Bypassed SDK 404 issues |
| **Correlation IDs** | Observability | ⏳ Next | |
| **Secret-less Vault Access** | Security | 📅 Planned | |

---
*Created on: 2026-01-26*
