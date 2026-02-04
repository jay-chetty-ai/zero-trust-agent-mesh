# Zero Trust AI Agent Mesh: Project Overview

## 1. Executive Summary
This project implements a **Zero Trust Architecture for AI Agents**, replacing traditional API keys with cryptographic identities. By leveraging **SPIFFE (Secure Production Identity Framework for Everyone)** and **SPIRE**, we ensure that every workload (AI Agent) is authenticated, authorized, and observable based on its verifyable software identity, not just network location.

The system features a "Security Inspector" UI that provides real-time visualization of the mesh's security assertions, including Identity (SVIDs), Integrity (JWS Signatures), and Traceability (OpenTelemetry).

## 2. System Architecture
The application is composed of independent microservices (Agents) running in a trusted mesh:

*   **SPIRE Infrastructure**: The underlying trust control plane.
    *   **SPIRE Server**: The Certificate Authority (CA) managing the trust domain.
    *   **SPIRE Agent**: Performs workload attestation and issues short-lived X.509 certificates (SVIDs).
*   **The AI Agents**:
    *   **Frontend Service**: The security gateway. Authenticates human users via **OAuth 2.0** and acts as the entry point to the mesh.
    *   **Researcher Agent**: Performs external research using the Tavily Search API.
    *   **Writer Agent**: Synthesizes information using the Google Gemini API.
*   **Security & Observability**:
    *   **mTLS**: All internal communication is mutually authenticated and encrypted.
    *   **OpenTelemetry**: Provides end-to-end distributed tracing.


<div style="page-break-before: always;"></div>

### Architecture Diagram
*(Rendered as ASCII for universal compatibility)*

```text
                     User (Human) / Browser
                              │
                              │ HTTPS (OAuth 2.0 Token)
                              ▼
        ================== TRUST BOUNDARY ============================
       ║                                                               ║
       ║           +------------------+                                ║
       ║           | Frontend Gateway | ────────────────────┐          ║
       ║           +------------------+                     │          ║
       ║                    │                               │          ║
       ║                    │ mTLS (SVID)                   │          ║
       ║                    ▼                               │          ║
       ║           +------------------+      Attest         │          ║
       ║           | Researcher Agent | ──────────────────> │          ║
       ║           +------------------+                     ▼          ║
       ║             │    │                           +-------------+  ║
       ║       HTTPS │    │ mTLS             Attest   | SPIRE Agent |  ║
       ║    (API Key)│    ▼              ┌──────────> |    (UDS)    |  ║
       ║             │  +--------------+ │            +-------------+  ║
       ║             │  | Writer Agent | ┘                   │         ║
       ║             │  +--------------+                     │ Node    ║
       ║             │         │                             │ Attest  ║
       ║             │         │ HTTPS (API Key)             ▼         ║
       ║             │         │                      +--------------+ ║
       ║             │         │                      | SPIRE Server | ║
       ║             │         │                      |     (CA)     | ║
       ║             │         │                      +--------------+ ║
       ║             │         │                                       ║
        =============│=========│=======================================
                     │         │
                     ▼         ▼
               Tavily API    Gemini API
              (External)     (External)
```

## 3. Implemented Security Features
These features are fully operational and demonstrable in the current build, validated by code analysis:

### User & Identity Management
1.  **OAuth 2.0 User Authentication**:
    *   The Frontend acts as an OIDC Client, authenticating human users (e.g., via Google) before granting access to the system.
    *   **Identity Bridging**: The authenticated user session is converted into an internal **Mesh JWT** signed by the Frontend's private key.
2.  **Automated SVID Rotation**:
    *   `src/common/spiffe.py`: A `SpiffeHelper` background thread connects to the Workload API and automatically rotates X.509 certificates before they expire, ensuring credential freshness without restart.

### Network & Transport Security
3.  **Strict Mutual TLS (mTLS)**:
    *   **Zero Trust Enforcement**: The `AgentServer` base class enforces `ssl.CERT_REQUIRED`. No connection is accepted without a valid client certificate.
    *   **Trust Bundle Validation**: Peers are validated against the SPIRE Trust Bundle, not public CAs.
4.  **Decorator-Based Authorization**:
    *   `src/common/server.py`: Uses `@require_identity(...)` decorators to enforce strict allow-lists of SPIFFE IDs on a per-endpoint basis.

### Data Integrity & Non-Repudiation
5.  **Cryptographic Response Signing (JWS)**:
    *   Agents sign their JSON responses using their ephemeral SVID private key.
    *   **Embedded Trust Chain**: The JWS header includes the `x5c` certificate chain, allowing the Frontend to verify both the signature *and* the identity of the signing agent (e.g., verifying that the Researcher Agent actually produced the research).
6.  **JWKS Key Distribution**:
    *   The Frontend exposes a `.well-known/jwks.json` style endpoint (`/debug/jwks`) over mTLS. Agents dynamically fetch public keys to verify User JWTs.

### Observability
7.  **Distributed Tracing (OpenTelemetry)**:
    *   Trace IDs are propagated via W3C `TraceContext` headers, linking user requests through the entire chain of agents.
8.  **Security Inspector UI**:
    *   A dedicated real-time visualizer in the Frontend to inspect SVIDs, parsed JWTs, and verification statuses.

## 4. Security Roadmap (Planned)
The following features are prioritized for upcoming phases to further harden the system:

1.  **Secret-less API Access**:
    *   Integration with **HashiCorp Vault** via SPIFFE Auth.
    *   Eliminates static `.env` secrets by fetching short-lived credentials dynamically.
2.  **Supply Chain Security (Sigstore/Cosign)**:
    *   Enforce "Code Provenance" by verifying container signatures before workload startup.
    *   SPIRE Workload Attestor will validate `cosign` signatures.
3.  **Data Guardrails (DLP)**:
    *   Automated scanning of prompts and responses for PII (Personally Identifiable Information) or secret leakage.
4.  **Network Egress Filtering**:
    *   Lock down outbound traffic to only allowlisted domains (e.g., `generativelanguage.googleapis.com`) using a SPIFFE-aware proxy.
5.  **Policy-as-Code (OPA)**:
    *   Centralized, dynamic authorization policies using Open Policy Agent, replacing hardcoded allow-lists.
