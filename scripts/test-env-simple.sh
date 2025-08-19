#!/bin/bash

# Simple .env coordination test
echo "🔍 Testing .env Coordination..."

# Function to extract value from .env file
get_env_value() {
    local file="$1"
    local key="$2"
    
    if [ -f "$file" ]; then
        grep "^$key=" "$file" | cut -d'=' -f2- | tr -d '"' | head -1
    else
        echo "NOTFOUND"
    fi
}

echo ""
echo "📊 Current Configuration:"
echo "========================="

# Root .env
echo "ROOT .env:"
echo "  FRONTEND_PORT: $(get_env_value '.env' 'FRONTEND_PORT')"
echo "  BACKEND_PORT: $(get_env_value '.env' 'BACKEND_PORT')"
echo "  CORS_ALLOWED_ORIGINS: $(get_env_value '.env' 'CORS_ALLOWED_ORIGINS')"

# Backend .env
echo ""
echo "BACKEND .env:"
echo "  PORT: $(get_env_value 'backend/.env' 'PORT')"
echo "  HOST: $(get_env_value 'backend/.env' 'HOST')"
echo "  ENVIRONMENT: $(get_env_value 'backend/.env' 'ENVIRONMENT')"

# Frontend .env
echo ""
echo "FRONTEND .env:"
echo "  VITE_API_URL: $(get_env_value 'frontend/.env' 'VITE_API_URL')"
echo "  VITE_FRONTEND_PORT: $(get_env_value 'frontend/.env' 'VITE_FRONTEND_PORT')"
echo "  VITE_BACKEND_PORT: $(get_env_value 'frontend/.env' 'VITE_BACKEND_PORT')"

echo ""
echo "✅ Key Checks:"
echo "=============="

# Critical checks
ROOT_CORS=$(get_env_value '.env' 'CORS_ALLOWED_ORIGINS')
BACKEND_PORT=$(get_env_value 'backend/.env' 'PORT')
FRONTEND_API_URL=$(get_env_value 'frontend/.env' 'VITE_API_URL')

if [[ "$ROOT_CORS" == *"localhost:4000"* ]]; then
    echo "✅ CORS includes frontend port 4000"
else
    echo "❌ CORS missing frontend port 4000"
fi

if [ "$BACKEND_PORT" = "9000" ]; then
    echo "✅ Backend port is 9000"
else
    echo "❌ Backend port is not 9000 (found: $BACKEND_PORT)"
fi

if [ "$FRONTEND_API_URL" = "http://localhost:9000" ]; then
    echo "✅ Frontend API URL points to backend port 9000"
else
    echo "❌ Frontend API URL incorrect (found: $FRONTEND_API_URL)"
fi

echo ""
echo "🚀 Next Steps:"
echo "=============="
echo "1. Restart backend to load new CORS settings"
echo "2. Restart frontend to reload VITE_API_URL"
echo "3. Check browser console for CORS errors"