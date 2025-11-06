#!/bin/bash
# Test runner script for Discord Bot backend

set -e

echo "==================================="
echo "Discord Bot Backend Test Suite"
echo "==================================="
echo ""

# Check if running in docker or local
if [ -f "/.dockerenv" ]; then
    echo "Running in Docker container"
else
    echo "Running locally"
    # Activate virtual environment if it exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
fi

# Install test dependencies if needed
echo "Checking dependencies..."
pip install -q pytest pytest-asyncio pytest-cov

echo ""
echo "Running tests..."
echo "-----------------------------------"

# Run tests with coverage
pytest tests/ \
    -v \
    --tb=short \
    --cov=services \
    --cov-report=term-missing \
    --cov-report=html

echo ""
echo "==================================="
echo "Test run complete!"
echo "==================================="
echo ""
echo "Coverage report generated in htmlcov/index.html"
echo ""
