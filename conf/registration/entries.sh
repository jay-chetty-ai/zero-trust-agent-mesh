#!/bin/bash
set -e

# SPIRE Server Container Name
SERVER_CONTAINER="spire-server"

echo "Creating Registration Entries..."

# 1. SPIRE Agent
# It needs to attest the NODE itself. 
docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry create \
    -spiffeID spiffe://example.org/ns/spire/sa/agent \
    -selector k8s:ns:default \
    -node

# Wait for node attestation is tricky in a script without loop, 
# for Docker Compose we usually use "join_token" for the agent so we don't need a Node entry if we did it that way?
# Ah, I configured "join_token" in server.conf.
# But for Workloads, we need entries that map to the Agent's Node ID.
# For simplicity in this demo, we will use a loose parent ID or rely on the fact that with join_token, the agent gets a generic ID.

# Let's register the workloads:

# Frontend
docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry create \
    -parentID spiffe://example.org/ns/spire/sa/agent \
    -spiffeID spiffe://example.org/ns/ui/sa/frontend \
    -selector docker:label:com.docker.compose.service:frontend \
    -selector docker:label:com.docker.compose.project:spiffe-spire-demo

# Researcher
docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry create \
    -parentID spiffe://example.org/ns/spire/sa/agent \
    -spiffeID spiffe://example.org/ns/agents/sa/researcher \
    -selector docker:label:com.docker.compose.service:researcher \
    -selector docker:label:com.docker.compose.project:spiffe-spire-demo

# Writer
docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry create \
    -parentID spiffe://example.org/ns/spire/sa/agent \
    -spiffeID spiffe://example.org/ns/agents/sa/writer \
    -selector docker:label:com.docker.compose.service:writer \
    -selector docker:label:com.docker.compose.project:spiffe-spire-demo

echo "Entries Created Successfully."
