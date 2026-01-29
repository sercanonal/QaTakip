#!/bin/bash

echo "=========================================="
echo "QA Task Manager - Production Test Suite"
echo "=========================================="
echo ""

BACKEND_URL="https://api.qataskmanager.com"
FRONTEND_URL="https://app.qataskmanager.com"

# Test 1: Backend Health Check
echo "1️⃣ Testing Backend Health..."
echo "URL: ${BACKEND_URL}/api/health"
HEALTH=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/api/health")
HTTP_CODE=$(echo "$HEALTH" | tail -n1)
BODY=$(echo "$HEALTH" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Backend is healthy!"
    echo "Response: $BODY"
else
    echo "❌ Backend health check failed (HTTP $HTTP_CODE)"
    echo "Response: $BODY"
fi
echo ""

# Test 2: Jira Connection Test
echo "2️⃣ Testing Jira Connection..."
echo "URL: ${BACKEND_URL}/api/jira/test-connection?username=SERCANO"
JIRA_TEST=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/api/jira/test-connection?username=SERCANO")
HTTP_CODE=$(echo "$JIRA_TEST" | tail -n1)
BODY=$(echo "$JIRA_TEST" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Jira test endpoint responded!"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "❌ Jira test failed (HTTP $HTTP_CODE)"
    echo "Response: $BODY"
fi
echo ""

# Test 3: Jira Server Connectivity (VPN Check)
echo "3️⃣ Testing Jira Server Connectivity (VPN Check)..."
echo "URL: https://jira.intertech.com.tr"
JIRA_CONN=$(curl -I -s -w "%{http_code}" -o /dev/null --connect-timeout 10 "https://jira.intertech.com.tr")

if [ "$JIRA_CONN" = "200" ] || [ "$JIRA_CONN" = "302" ] || [ "$JIRA_CONN" = "301" ]; then
    echo "✅ Jira server is reachable! (HTTP $JIRA_CONN)"
    echo "VPN connection is working!"
else
    echo "❌ Cannot reach Jira server (HTTP $JIRA_CONN)"
    echo "VPN might not be configured or Jira is down"
fi
echo ""

# Test 4: User Info Check
echo "4️⃣ Testing User Info (SERCANO Admin Check)..."
echo "URL: ${BACKEND_URL}/api/debug/user-info?name=sercano"
USER_INFO=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/api/debug/user-info?name=sercano")
HTTP_CODE=$(echo "$USER_INFO" | tail -n1)
BODY=$(echo "$USER_INFO" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ User info endpoint responded!"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    
    # Check if SERCANO is admin
    if echo "$BODY" | grep -q '"role": "admin"'; then
        echo "✅ SERCANO is Admin!"
    else
        echo "⚠️  SERCANO role is NOT admin"
    fi
else
    echo "❌ User info check failed (HTTP $HTTP_CODE)"
    echo "Response: $BODY"
fi
echo ""

# Test 5: Frontend Accessibility
echo "5️⃣ Testing Frontend Accessibility..."
echo "URL: ${FRONTEND_URL}"
FRONTEND=$(curl -I -s -w "%{http_code}" -o /dev/null --connect-timeout 10 "${FRONTEND_URL}")

if [ "$FRONTEND" = "200" ]; then
    echo "✅ Frontend is accessible! (HTTP $FRONTEND)"
else
    echo "❌ Frontend not accessible (HTTP $FRONTEND)"
fi
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "Next Steps:"
echo "1. If Jira test shows issues_found > 0: ✅ Jira sync will work!"
echo "2. If VPN check failed: Configure VPN on your server"
echo "3. If SERCANO is not admin: Check database or re-login"
echo "4. Wait 15 minutes for automatic Jira sync or trigger manual sync"
echo ""
echo "Manual Jira Sync Command:"
echo "curl -X POST \"${BACKEND_URL}/api/jira/sync-now?user_id=YOUR_USER_ID\""
echo ""
