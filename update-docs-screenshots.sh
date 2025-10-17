#!/bin/bash
# Update documentation screenshots
# Run this whenever you want to refresh all documentation images

echo "🎬 Starting Broadlink Manager for screenshots..."

# Start the app in background (adjust command as needed)
cd app
python main.py &
APP_PID=$!

# Wait for app to start
echo "⏳ Waiting for app to start..."
sleep 5

# Run screenshot tests
echo "📸 Capturing screenshots..."
cd ..
pytest tests/e2e/test_documentation_screenshots.py -v -m docs

# Stop the app
echo "🛑 Stopping app..."
kill $APP_PID

echo "✅ Screenshots updated in docs/images/screenshots/"
echo "📁 Check the following files:"
ls -lh docs/images/screenshots/
