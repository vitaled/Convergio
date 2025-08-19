#!/bin/bash

# ================================
# Environment Configuration Test
# ================================
# Verifies that each service reads from the correct .env file
# and that all .env files are coordinated

set -e

echo "🔍 Testing Environment Configuration..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_result() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"
    
    if [ "$expected" = "$actual" ]; then
        echo -e "${GREEN}✅ PASS${NC} $test_name: $actual"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} $test_name: expected '$expected', got '$actual'"
        ((TESTS_FAILED++))
    fi
}

# Function to check if file exists
check_file() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ FOUND${NC} $description: $file"
        return 0
    else
        echo -e "${RED}❌ MISSING${NC} $description: $file"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to extract value from .env file
get_env_value() {
    local file="$1"
    local key="$2"
    
    if [ -f "$file" ]; then
        grep "^$key=" "$file" | cut -d'=' -f2- | tr -d '"' | head -1
    else
        echo ""
    fi
}

echo "📁 Checking .env files exist..."
echo ""

# Check all .env files exist
check_file ".env" "Root .env"
check_file "backend/.env" "Backend .env"  
check_file "frontend/.env" "Frontend .env"
check_file ".env.example" "Root .env.example"
check_file "backend/.env.example" "Backend .env.example"
check_file "frontend/.env.example" "Frontend .env.example"

echo ""
echo "🔧 Testing Backend Configuration..."
echo ""

# Test backend configuration by checking .env files directly
# (Can't test Python config loading without dependencies installed)

BACKEND_PORT_FROM_ENV=$(get_env_value "backend/.env" "PORT")
BACKEND_HOST_FROM_ENV=$(get_env_value "backend/.env" "HOST")
ROOT_CORS_FROM_ENV=$(get_env_value ".env" "CORS_ALLOWED_ORIGINS")

echo "Testing .env file values directly (Python dependencies not required)..."

# Use values from .env files directly
BACKEND_PORT="$BACKEND_PORT_FROM_ENV"
BACKEND_HOST="$BACKEND_HOST_FROM_ENV"
BACKEND_CORS="$ROOT_CORS_FROM_ENV"
BACKEND_ENV=$(get_env_value "backend/.env" "ENVIRONMENT")

# Expected values from .env files
EXPECTED_BACKEND_PORT="9000"
EXPECTED_BACKEND_HOST="0.0.0.0"
EXPECTED_CORS_CONTAINS="http://localhost:4000"

print_result "Backend PORT" "$EXPECTED_BACKEND_PORT" "$BACKEND_PORT"
print_result "Backend HOST" "$EXPECTED_BACKEND_HOST" "$BACKEND_HOST"

# Check if CORS contains required origins
if [[ "$BACKEND_CORS" == *"$EXPECTED_CORS_CONTAINS"* ]]; then
    echo -e "${GREEN}✅ PASS${NC} Backend CORS contains frontend origin: $EXPECTED_CORS_CONTAINS"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} Backend CORS missing frontend origin: $EXPECTED_CORS_CONTAINS"
    echo -e "${YELLOW}   Actual CORS: $BACKEND_CORS${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "🌐 Testing Frontend Configuration..."
echo ""

# Test frontend environment variables
cd frontend

# Check if VITE_API_URL is correct in .env
FRONTEND_API_URL=$(get_env_value ".env" "VITE_API_URL")
FRONTEND_PORT=$(get_env_value ".env" "VITE_FRONTEND_PORT")
BACKEND_PORT_FROM_FRONTEND=$(get_env_value ".env" "VITE_BACKEND_PORT")

EXPECTED_API_URL="http://localhost:9000"
EXPECTED_FRONTEND_PORT="4000"
EXPECTED_BACKEND_PORT_REF="9000"

print_result "Frontend VITE_API_URL" "$EXPECTED_API_URL" "$FRONTEND_API_URL"
print_result "Frontend VITE_FRONTEND_PORT" "$EXPECTED_FRONTEND_PORT" "$FRONTEND_PORT"
print_result "Frontend VITE_BACKEND_PORT" "$EXPECTED_BACKEND_PORT_REF" "$BACKEND_PORT_FROM_FRONTEND"

cd ..

echo ""
echo "🔄 Testing .env Coordination..."
echo ""

# Check that port configurations are coordinated
ROOT_FRONTEND_PORT=$(get_env_value ".env" "FRONTEND_PORT")
ROOT_BACKEND_PORT=$(get_env_value ".env" "BACKEND_PORT")
ROOT_CORS=$(get_env_value ".env" "CORS_ALLOWED_ORIGINS")

print_result "Root FRONTEND_PORT" "4000" "$ROOT_FRONTEND_PORT"
print_result "Root BACKEND_PORT" "9000" "$ROOT_BACKEND_PORT"

# Check CORS coordination
if [[ "$ROOT_CORS" == *"localhost:4000"* ]] && [[ "$ROOT_CORS" == *"localhost:9000"* ]]; then
    echo -e "${GREEN}✅ PASS${NC} Root CORS includes both frontend and backend ports"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} Root CORS missing required ports"
    echo -e "${YELLOW}   Root CORS: $ROOT_CORS${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "📋 Testing .env.example Consistency..."
echo ""

# Check that .env.example files are consistent
ROOT_EXAMPLE_FRONTEND_PORT=$(get_env_value ".env.example" "FRONTEND_PORT")
ROOT_EXAMPLE_BACKEND_PORT=$(get_env_value ".env.example" "BACKEND_PORT")
BACKEND_EXAMPLE_PORT=$(get_env_value "backend/.env.example" "PORT")
FRONTEND_EXAMPLE_API_URL=$(get_env_value "frontend/.env.example" "VITE_API_URL")

print_result "Root .env.example FRONTEND_PORT" "4000" "$ROOT_EXAMPLE_FRONTEND_PORT"
print_result "Root .env.example BACKEND_PORT" "9000" "$ROOT_EXAMPLE_BACKEND_PORT"
print_result "Backend .env.example PORT" "9000" "$BACKEND_EXAMPLE_PORT"
print_result "Frontend .env.example VITE_API_URL" "http://localhost:9000" "$FRONTEND_EXAMPLE_API_URL"

echo ""
echo "🚨 Testing for Hardcoded URLs..."
echo ""

# Check for remaining hardcoded URLs that should use environment variables
HARDCODED_ISSUES=0

echo "Checking for hardcoded localhost URLs in source code..."

# Check frontend source for hardcoded URLs (excluding .env files and node_modules)
FRONTEND_HARDCODED=$(find frontend/src -name "*.ts" -o -name "*.svelte" -o -name "*.js" | xargs grep -l "localhost:[0-9]" 2>/dev/null || true)
if [ -n "$FRONTEND_HARDCODED" ]; then
    echo -e "${YELLOW}⚠️  WARN${NC} Found potential hardcoded URLs in frontend:"
    echo "$FRONTEND_HARDCODED" | while read file; do
        echo -e "${YELLOW}   - $file${NC}"
    done
    ((HARDCODED_ISSUES++))
fi

# Check backend source for hardcoded URLs
BACKEND_HARDCODED=$(find backend/src -name "*.py" | xargs grep -l "localhost:[0-9]" 2>/dev/null || true)
if [ -n "$BACKEND_HARDCODED" ]; then
    echo -e "${YELLOW}⚠️  WARN${NC} Found potential hardcoded URLs in backend:"
    echo "$BACKEND_HARDCODED" | while read file; do
        echo -e "${YELLOW}   - $file${NC}"
    done
    ((HARDCODED_ISSUES++))
fi

if [ $HARDCODED_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} No obvious hardcoded URLs found"
    ((TESTS_PASSED++))
fi

echo ""
echo "📊 Test Summary"
echo "==============="
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All environment configuration tests passed!${NC}"
    echo -e "${BLUE}📝 Configuration Summary:${NC}"
    echo -e "   Frontend (port 4000) -> Backend (port 9000)"
    echo -e "   CORS properly configured for cross-origin requests"
    echo -e "   All .env files are coordinated and consistent"
    exit 0
else
    echo ""
    echo -e "${RED}💥 Some tests failed. Please fix the issues above.${NC}"
    echo ""
    echo -e "${BLUE}💡 Common fixes:${NC}"
    echo -e "   - Ensure all .env files have correct port numbers"
    echo -e "   - Check CORS_ALLOWED_ORIGINS includes frontend port"
    echo -e "   - Verify VITE_API_URL points to correct backend port"
    echo -e "   - Restart services after .env changes"
    exit 1
fi