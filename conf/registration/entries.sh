#!/bin/bash
set -e

# SPIRE Server Container Name
SERVER_CONTAINER="spire-server"

echo "Creating Registration Entries..."

# Helper function to create entry only if it doesn't exist
create_entry() {
    local parent_id=$1
    local spiffe_id=$2
    local selector_service=$3
    
    # Check if entry exists
    if docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry show -spiffeID "$spiffe_id" > /dev/null 2>&1; then
        echo "Entry for $spiffe_id already exists. Skipping."
    else
        echo "Creating entry for $spiffe_id..."
        docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry create \
            -parentID "$parent_id" \
            -spiffeID "$spiffe_id" \
            -selector docker:label:com.docker.compose.service:"$selector_service" \
            -selector docker:label:com.docker.compose.project:spiffe-spire-demo
    fi
}

# We do NOT need to create the Node entry manually when using join tokens in this configuration,
# or if we do, it should match the token generation. 
# However, for this demo, the Agent has already joined and has the ID 'spiffe://example.org/ns/spire/sa/agent'.
# We just need to register the workloads under that Parent ID.

# Register Workloads
create_entry "spiffe://example.org/ns/spire/sa/agent" "spiffe://example.org/ns/ui/sa/frontend" "frontend"
create_entry "spiffe://example.org/ns/spire/sa/agent" "spiffe://example.org/ns/agents/sa/researcher" "researcher"
create_entry "spiffe://example.org/ns/spire/sa/agent" "spiffe://example.org/ns/agents/sa/writer" "writer"

echo "Registration Complete."
