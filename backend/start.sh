#!/bin/bash
# Startup script for NoFeesApts backend
# Ensures Playwright browsers are installed before starting the server

echo "Checking Playwright browser installation..."

# Set the browsers path
export PLAYWRIGHT_BROWSERS_PATH=/pw-browsers

# Check if chromium is installed
if [ ! -d "$PLAYWRIGHT_BROWSERS_PATH/chromium-1194" ] && [ ! -d "$PLAYWRIGHT_BROWSERS_PATH/chromium_headless_shell-1194" ]; then
    echo "Installing Playwright Chromium browser..."
    playwright install chromium
    echo "Playwright browser installed successfully"
else
    echo "Playwright browser already installed"
fi

# Start the server
echo "Starting FastAPI server..."
exec uvicorn server:app --host 0.0.0.0 --port 8001
