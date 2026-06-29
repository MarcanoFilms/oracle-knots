#!/bin/bash
# Oracle Knots GUI Test Runner
# Runs unit tests, integration tests, and generates coverage reports

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=================================================="
echo "Oracle Knots GUI - Test Suite"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found, installing...${NC}"
    pip install pytest pytest-cov
fi

echo -e "${YELLOW}Test Suite: Unit Tests${NC}"
echo "=================================================="

# Run unit tests
UNIT_TESTS=(
    "test_dashboard_api.py"
    "test_wallet_api.py"
    "test_config_api.py"
    "test_security_validation.py"
)

PASSED=0
FAILED=0

for test_file in "${UNIT_TESTS[@]}"; do
    if [ -f "$SCRIPT_DIR/$test_file" ]; then
        echo ""
        echo "Running: $test_file"
        if python -m pytest "$SCRIPT_DIR/$test_file" -v --tb=short; then
            PASSED=$((PASSED + 1))
            echo -e "${GREEN}✓ $test_file passed${NC}"
        else
            FAILED=$((FAILED + 1))
            echo -e "${RED}✗ $test_file failed${NC}"
        fi
    fi
done

echo ""
echo "=================================================="
echo -e "${YELLOW}Test Summary${NC}"
echo "=================================================="
echo "Unit Tests Passed: $PASSED"
echo "Unit Tests Failed: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"

    # Run coverage if pytest-cov is available
    if python -m pip show pytest-cov &> /dev/null; then
        echo ""
        echo -e "${YELLOW}Generating coverage report...${NC}"
        python -m pytest "$SCRIPT_DIR" --cov=gui --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
    fi

    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
