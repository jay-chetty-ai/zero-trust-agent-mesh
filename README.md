# SPIFFE/SPIRE AI Agent Demo

A secure, agentic AI application demonstrating **Zero Trust** principles using **SPIFFE** (Secure Production Identity Framework for Everyone) and **SPIRE**.

This project implements a multi-agent system where Python AI agents run as independent services and authenticate each other using cryptographic identities (SVIDs) sourced from the **SPIRE Workload API**.

## Features

*   **Zero Trust Networking**: No static API keys between services. All service-to-service communication is secured via mTLS using SPIFFE IDs.
*   **Decoupled Agents**:
    *   **Researcher**: Uses Tavily Search to gather information based on user queries.
    *   **Writer**: Generates structured content (blog posts) using the **Gemini 2.0 Flash** model via direct REST API integration.
*   **Secure Orchestration**: A frontend application coordinates the workflow, bridging Human Auth (Mock OAuth) to Machine Auth (SPIFFE).
*   **A2A Security**: Strict SPIFFE ID validation at every hop (Frontend → Researcher → Writer).
*   **Local Simulation**: Full SPIFFE infrastructure runs locally on Linux using Docker Compose.

## Architecture

![Architecture](SYSTEM.md)

See [SYSTEM.md](SYSTEM.md) for a deep dive into the security design and SPIFFE concepts.

## Getting Started

To run this application, you need Docker and Docker Compose installed on your system.

See [SETUP.md](SETUP.md) for detailed installation and usage instructions.

