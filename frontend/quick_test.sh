#!/bin/bash
# Quick Vista3D Connectivity Test

echo "======================================================================"
echo "Vista3D Quick Connectivity Test"
echo "======================================================================"
echo ""

echo "1️⃣  Frontend Container → Backend:"
HTTP_CODE=$(docker exec vista3d-frontend-standalone curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://host.docker.internal:8000/v1/vista3d/info 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ PASS - HTTP $HTTP_CODE"
else
    echo "   ❌ FAIL - HTTP $HTTP_CODE"
fi

echo ""
echo "2️⃣  SSH Tunnel Status:"
if ps aux | grep -q "[s]sh.*8000.*8888"; then
    echo "   ✅ PASS - SSH tunnel is running"
    ps aux | grep "[s]sh.*8000.*8888" | head -1
else
    echo "   ❌ FAIL - No SSH tunnel found"
    echo "   Start: ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@server"
fi

echo ""
echo "3️⃣  Backend Reachable from Mac:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8000/v1/vista3d/info 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ PASS - HTTP $HTTP_CODE"
else
    echo "   ❌ FAIL - HTTP $HTTP_CODE"
fi

echo ""
echo "4️⃣  Image Server Reachable from Mac:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost:8888/health 2>&1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ PASS - HTTP $HTTP_CODE"
else
    echo "   ❌ FAIL - HTTP $HTTP_CODE"
fi

echo ""
echo "======================================================================"
echo "DIAGNOSIS:"
echo "======================================================================"
echo ""
echo "If tests 1, 2, 3, and 4 all PASS, but segmentation still fails,"
echo "then the issue is the REVERSE SSH tunnel on the Ubuntu server."
echo ""
echo "The backend on Ubuntu cannot reach localhost:8888."
echo ""
echo "FIX: On Ubuntu server, check:"
echo "  1. netstat -tln | grep 8888    (should show port listening)"
echo "  2. SSH config needs: GatewayPorts clientspecified"
echo "  3. Reconnect SSH with: -R 8888:0.0.0.0:8888"
echo ""

