#!/bin/bash
set -e

echo "🛑 Stopping all services..."
docker compose down

echo "🚀 Starting SPIRE Infrastructure and Agents..."
docker compose up -d

echo "⏳ Waiting 5 seconds for SPIRE Server to initialize..."
sleep 5

echo "📝 Registering Workload Entries..."
bash conf/registration/entries.sh

echo "✅ Demo Environment is Ready!"
echo "   - Frontend UI: http://localhost:8501"
echo "   - Attack Simulation: docker exec frontend-app python src/attack_simulation.py"

echo -e "\n🔍 Verify Status"
echo "   Check if agents have received their SVIDs by running:"
echo ""
echo "   (You should see logs indicating 'SVID Updated' or 'Success: AgentServer is running')"
bash docker compose logs -f researcher"
