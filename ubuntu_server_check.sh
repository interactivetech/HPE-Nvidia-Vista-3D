#!/bin/bash
# Run this script ON THE UBUNTU SERVER to diagnose the reverse tunnel issue

echo "========================================================================"
echo "Ubuntu Server - Reverse SSH Tunnel Diagnostic"
echo "========================================================================"
echo ""

# Test 1: Check SSH config
echo "1️⃣  SSH Server Configuration:"
echo "----------------------------------------"
GATEWAY_SETTING=$(grep -i "^GatewayPorts" /etc/ssh/sshd_config 2>/dev/null)
if [ -n "$GATEWAY_SETTING" ]; then
    echo "✅ Found: $GATEWAY_SETTING"
    if echo "$GATEWAY_SETTING" | grep -qi "yes\|clientspecified"; then
        echo "   ✅ Setting is correct"
    else
        echo "   ❌ Setting is wrong - should be 'yes' or 'clientspecified'"
        echo "   Fix: sudo nano /etc/ssh/sshd_config"
        echo "   Add: GatewayPorts clientspecified"
        echo "   Then: sudo systemctl restart sshd"
    fi
else
    echo "❌ GatewayPorts not set in config"
    echo "   Fix: sudo nano /etc/ssh/sshd_config"
    echo "   Add: GatewayPorts clientspecified"
    echo "   Then: sudo systemctl restart sshd"
fi
echo ""

# Test 2: Check if port 8888 is listening
echo "2️⃣  Port 8888 Listening Status:"
echo "----------------------------------------"
if command -v netstat &> /dev/null; then
    LISTEN_CHECK=$(netstat -tln 2>/dev/null | grep ":8888")
elif command -v ss &> /dev/null; then
    LISTEN_CHECK=$(ss -tln 2>/dev/null | grep ":8888")
else
    LISTEN_CHECK=""
fi

if [ -n "$LISTEN_CHECK" ]; then
    echo "✅ Port 8888 is listening:"
    echo "$LISTEN_CHECK"
    
    # Check if it's listening on 0.0.0.0 (required for Docker)
    if echo "$LISTEN_CHECK" | grep -q "0.0.0.0:8888"; then
        echo "   ✅ Listening on 0.0.0.0 (Docker containers can access it)"
    elif echo "$LISTEN_CHECK" | grep -q "127.0.0.1:8888"; then
        echo "   ❌ Only listening on 127.0.0.1 (Docker containers CANNOT access it)"
        echo "   Fix: Reconnect SSH with: -R 8888:0.0.0.0:8888"
        echo "        NOT: -R 8888:localhost:8888"
    fi
else
    echo "❌ Port 8888 is NOT listening"
    echo "   Reverse SSH tunnel is not active"
    echo "   From your Mac, run:"
    echo "   ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@this-server"
fi
echo ""

# Test 3: Test from localhost
echo "3️⃣  Test Connection from Ubuntu localhost:"
echo "----------------------------------------"
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8888/health 2>&1)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ localhost:8888 is reachable (HTTP $HTTP_CODE)"
    else
        echo "❌ localhost:8888 is NOT reachable (HTTP $HTTP_CODE)"
        echo "   Reverse tunnel is not working"
    fi
else
    echo "⚠️  curl not installed, skipping test"
fi
echo ""

# Test 4: Test from Docker container (if running)
echo "4️⃣  Test from Vista3D Docker Container:"
echo "----------------------------------------"
if command -v docker &> /dev/null; then
    CONTAINER=$(docker ps --filter "name=vista3d" --format "{{.Names}}" | head -1)
    if [ -n "$CONTAINER" ]; then
        echo "Found container: $CONTAINER"
        HTTP_CODE=$(docker exec "$CONTAINER" curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8888/health 2>&1)
        if [ "$HTTP_CODE" = "200" ]; then
            echo "✅ Container can reach localhost:8888 (HTTP $HTTP_CODE)"
            echo "   🎉 REVERSE TUNNEL IS WORKING!"
        else
            echo "❌ Container CANNOT reach localhost:8888 (HTTP $HTTP_CODE)"
            echo "   This is why segmentation fails!"
            echo ""
            echo "   Common causes:"
            echo "   1. GatewayPorts not set to 'clientspecified' or 'yes'"
            echo "   2. SSH tunnel using -R 8888:localhost:8888 instead of -R 8888:0.0.0.0:8888"
            echo "   3. SSH tunnel not reconnected after config change"
        fi
    else
        echo "⚠️  No Vista3D container running"
        echo "   Start it with: docker compose up -d"
    fi
else
    echo "⚠️  Docker not installed or not accessible"
fi
echo ""

# Test 5: Check SSH connections
echo "5️⃣  Active SSH Connections:"
echo "----------------------------------------"
if command -v who &> /dev/null; then
    SSH_USERS=$(who | grep -v "^$" | wc -l)
    echo "Active SSH sessions: $SSH_USERS"
    who
fi
echo ""

# Summary
echo "========================================================================"
echo "SUMMARY & ACTION ITEMS"
echo "========================================================================"
echo ""

if [ -z "$GATEWAY_SETTING" ] || ! echo "$GATEWAY_SETTING" | grep -qi "yes\|clientspecified"; then
    echo "❌ STEP 1: Enable GatewayPorts"
    echo "   sudo nano /etc/ssh/sshd_config"
    echo "   Add line: GatewayPorts clientspecified"
    echo "   sudo systemctl restart sshd"
    echo ""
fi

if [ -z "$LISTEN_CHECK" ]; then
    echo "❌ STEP 2: Establish reverse SSH tunnel from your Mac"
    echo "   ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@$(hostname)"
    echo ""
elif echo "$LISTEN_CHECK" | grep -q "127.0.0.1:8888"; then
    echo "❌ STEP 2: Reconnect SSH with correct binding"
    echo "   Current tunnel only binds to 127.0.0.1"
    echo "   Disconnect and reconnect with: -R 8888:0.0.0.0:8888"
    echo ""
fi

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ STEP 3: After fixing above, test again with this script"
    echo ""
fi

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Everything looks good from Ubuntu's perspective!"
    echo "   If segmentation still fails, check the frontend/Mac side."
fi

echo "========================================================================"

