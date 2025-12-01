#!/bin/bash
# Quick script to test the website locally

echo "🚀 Starting local web server..."
echo "📂 Serving from: docs/"
echo "🌐 Open your browser to: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")/.." && python3 -m http.server 8000 --directory docs
