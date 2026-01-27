#!/bin/bash
set -e

# SPIRE Server Container Name
SERVER_CONTAINER="spire-server"

echo "Creating Registration Entries..."

# Helper function to create entry only if it doesn't exist
create_entry() {
    local parent_id=$1
    local spiffe_id=$2
    local container_name=$3
    
    # 1. Get the Image ID (Name) from the running container
    #    In Docker Compose local dev, SPIRE sees the Image Name (Config.Image) as the ID, not the SHA.
    local image_id
    if ! image_id=$(docker inspect --format='{{.Config.Image}}' "$container_name" 2>/dev/null); then
        echo "Error: Could not find container '$container_name'. Is it running?"
        return 1
    fi

    # Determine if we need to recreate the entry
    if docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry show -spiffeID "$spiffe_id" > /dev/null 2>&1; then
        echo "Entry for $spiffe_id exists. Deleting to ensure we use the latest Image ID..."
        # Fetch Entry ID to delete it
        local entry_id
        entry_id=$(docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry show -spiffeID "$spiffe_id" \
            | grep "Entry ID" | head -n 1 | awk '{print $4}')
        
        if [ -n "$entry_id" ]; then
            docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry delete -entryID "$entry_id"
        fi
    fi

    echo "Creating entry for $spiffe_id..."
    echo "  -> Locked to Image ID: $image_id"
    
    docker exec $SERVER_CONTAINER /opt/spire/bin/spire-server entry create \
        -parentID "$parent_id" \
        -spiffeID "$spiffe_id" \
        -selector docker:image_id:"$image_id"
}

# We do NOT need to create the Node entry manually when using join tokens in this configuration,
# or if we do, it should match the token generation. 
# However, for this demo, the Agent has already joined and has the ID 'spiffe://example.org/ns/spire/sa/agent'.
# We just need to register the workloads under that Parent ID.

# Register Workloads
# NOTE: We now pass the container_name (from docker-compose.yaml) so we can look up its hash.
create_entry "spiffe://example.org/ns/spire/sa/agent" "spiffe://example.org/ns/ui/sa/frontend" "frontend-app"
create_entry "spiffe://example.org/ns/spire/sa/agent" "spiffe://example.org/ns/agents/sa/researcher" "research-agent"
create_entry "spiffe://example.org/ns/spire/sa/agent" "spiffe://example.org/ns/agents/sa/writer" "writer-agent"

echo "Registration Complete."
