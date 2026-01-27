#!/bin/bash
set -e

echo "🛑 Stopping all services..."
docker compose down

echo "🧹 Wiping old SPIRE data to ensure a clean state..."
# Use Docker to remove files to avoid permission issues (files owned by root/docker)
docker run --rm -v $(pwd):/work alpine sh -c "rm -rf /work/run/spire/data/server/* /work/run/spire/data/agent/*"

echo "🚀 Starting SPIRE Server..."
docker compose up -d spire-server

echo "⏳ Waiting 5 seconds for SPIRE Server to initialize..."
sleep 5

echo "🔑 Generating new Join Token..."
# Extract the token (second word of the output: "Token: <value>")
TOKEN=$(docker exec spire-server /opt/spire/bin/spire-server token generate -spiffeID spiffe://example.org/ns/spire/sa/agent | awk '{print $2}')
echo "   Token: $TOKEN"

echo "🚀 Starting SPIRE Agent and Workloads..."
export SPIRE_JOIN_TOKEN=$TOKEN
docker compose up -d

echo "⏳ Waiting 10 seconds for Agent and Workload Attestation..."
sleep 10

echo "📝 Registering Workload Entries..."
bash conf/registration/entries.sh

echo "✅ Demo Environment is Ready!"
echo "   - Frontend UI: http://localhost:8501"
echo "   - Attack Simulation: docker exec frontend-app python src/attack_simulation.py"

echo -e "\n🔍 Verify Status"
echo "   Check if agents have received their SVIDs by running:"
echo "   docker compose logs researcher --tail 5"
echo ""
echo "   (You should see logs indicating 'SVID Updated' or 'Success: AgentServer is running')"
