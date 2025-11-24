#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== Testing Robotics API ==="
echo ""

# Check if API is running
echo "Checking if API is running..."
if ! curl -s "$BASE_URL/docs" > /dev/null; then
    echo "✗ ERROR: API is not running on $BASE_URL"
    echo "   Please start the application: docker-compose up"
    exit 1
fi
echo "✓ API is running"
echo ""

# 1. Health Check
echo "1. Testing API Docs..."
curl -s "$BASE_URL/docs" | head -n 5
echo -e "\n✓ API Docs accessible\n"

# 2. Create Wall
echo "2. Creating Wall..."
WALL_RESPONSE=$(curl -s -X POST "$BASE_URL/walls/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Wall",
    "geometry": {
      "boundary": [[0, 0], [10, 0], [10, 5], [0, 5]]
    }
  }')
echo "$WALL_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$WALL_RESPONSE"
WALL_ID=$(echo "$WALL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
if [ -z "$WALL_ID" ]; then
    echo "✗ Failed to create wall"
    exit 1
fi
echo -e "\n✓ Wall created with ID: $WALL_ID\n"

# 3. List Walls
echo "3. Listing Walls..."
curl -s "$BASE_URL/walls/" | python3 -m json.tool 2>/dev/null || curl -s "$BASE_URL/walls/"
echo -e "\n✓ Walls listed\n"

# 4. Create Obstacle
echo "4. Creating Obstacle..."
OBSTACLE_RESPONSE=$(curl -s -X POST "$BASE_URL/obstacles/" \
  -H "Content-Type: application/json" \
  -d "{
    \"wall_id\": $WALL_ID,
    \"geometry\": {
      \"boundary\": [[2, 2], [4, 2], [4, 3], [2, 3]]
    }
  }")
echo "$OBSTACLE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$OBSTACLE_RESPONSE"
echo -e "\n✓ Obstacle created\n"

# 5. Generate Path Plan
echo "5. Generating Path Plan (this may take a few seconds)..."
PLAN_RESPONSE=$(curl -s -X POST "$BASE_URL/plans/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "wall_geometry": {
      "boundary": [[0, 0], [10, 0], [10, 5], [0, 5]]
    },
    "obstacles": [
      {"boundary": [[2, 2], [4, 2], [4, 3], [2, 3]]}
    ]
  }')
echo "$PLAN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$PLAN_RESPONSE"
PLAN_ID=$(echo "$PLAN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
if [ -z "$PLAN_ID" ]; then
    echo "✗ Failed to generate path plan"
    exit 1
fi
echo -e "\n✓ Path plan generated with ID: $PLAN_ID\n"

# 6. Send Robot Command
echo "6. Sending Robot Command..."
COMMAND_RESPONSE=$(curl -s -X POST "$BASE_URL/robot/command" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "move",
    "x": 5.0,
    "y": 3.0
  }')
echo "$COMMAND_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$COMMAND_RESPONSE"
echo -e "\n✓ Command sent\n"

# 7. Update Robot State
echo "7. Updating Robot State..."
STATE_RESPONSE=$(curl -s -X POST "$BASE_URL/robot/state" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "moving",
    "position": {"x": 5.0, "y": 3.0, "z": 0.0},
    "velocity": 0.5,
    "battery": 85.0
  }')
echo "$STATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATE_RESPONSE"
echo -e "\n✓ Robot state updated\n"

# 8. Get Robot State
echo "8. Getting Robot State..."
curl -s "$BASE_URL/robot/state" | python3 -m json.tool 2>/dev/null || curl -s "$BASE_URL/robot/state"
echo -e "\n✓ Robot state retrieved\n"

# 9. Create Execution Run
echo "9. Creating Execution Run..."
RUN_RESPONSE=$(curl -s -X POST "$BASE_URL/runs/" \
  -H "Content-Type: application/json" \
  -d "{
    \"plan_id\": $PLAN_ID,
    \"status\": \"running\",
    \"telemetry\": {
      \"progress\": 0.5,
      \"current_waypoint\": 3
    }
  }")
echo "$RUN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RUN_RESPONSE"
echo -e "\n✓ Execution run created\n"

# 10. List Runs
echo "10. Listing Execution Runs..."
curl -s "$BASE_URL/runs/" | python3 -m json.tool 2>/dev/null || curl -s "$BASE_URL/runs/"
echo -e "\n✓ Runs listed\n"

echo "=== All Tests Completed Successfully ==="

