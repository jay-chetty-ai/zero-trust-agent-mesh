# 🎭 Zero Trust Mesh Demo Script

This document outlines the steps to perform the "Three-Layer Reveal" demo for the Secure AI Agent Mesh.

## 🟢 Play 1: The Unified Thread (Distributed Tracing)

**Goal**: Show how requests are tracked across isolated containers.

1. Open two terminal windows.
2. **Terminal 1**: Tail the Researcher logs.
   ```bash
   docker logs -f research-agent
   ```
3. **Terminal 2**: Tail the Writer logs.
   ```bash
   docker logs -f writer-agent
   ```
4. **Action**: Go to the UI (localhost:8501) and ask a question (e.g., "What is Spiffe?").
5. **Reveal**: Point out the matching `[trace_id=...]` in both terminals.

---

## 🛡️ Play 2: The Identity Inspector (UI Visualization)

**Goal**: Make the invisible security layers (SPIFFE & JWS) visible.

1. In the Streamlit UI Sidebar, locate the **"Security Inspector"** section.
2. Toggle **"Enable Deep Inspection"**.
3. **Machine Identity**: 
   - Show the verified SPIFFE ID `spiffe://example.org/ns/ui/sa/frontend`.
   - Click **"View SVID Certificate"** to show the real PEM data.
4. **Human Identity**:
   - Show the decoded JWT (User ID: `user_alice`).
   - Explain how this propagates user context.
5. **Content Integrity**:
   - After a response, show the **"Security Audit Log"**.
   - Point out the `✓ Researcher JWS Verified` and `✓ Writer JWS Verified` events.

---

## 💀 Play 3: The Zero Trust Rejection (Attack Simulation)

**Goal**: Prove that the system actually blocks unauthorized access, even from inside the network.

1. **Scenario**: A compromised container (or malicious insider) tries to access the Agents.
2. **Run the Attack Script**:
   ```bash
   docker exec frontend-app python src/attack_simulation.py
   ```
3. **Expected Output**:
   - **Attack 1 (No JWT)**: `🛡️ BLOCKED! Server responded with 401.`
   - **Attack 2 (Forged JWT)**: `🛡️ BLOCKED! Server responded with 401.`

---
