#!/bin/bash
# Code Quality Checks Script
# Runs all linting, type checking, testing, and complexity analysis tools

echo "================================"
echo "Code Quality Checks"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
FAILED=0
PASSED=0

run_check() {
    local name=$1
    local command=$2

    echo -e "${YELLOW}Running: $name${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✓ $name passed${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ $name failed${NC}"
        ((FAILED++))
    fi
    echo ""
}

# 1. Ruff - Linting
run_check "Ruff (linting)" "uv run ruff check ."

# 2. Ruff - Formatting
run_check "Ruff (formatting check)" "uv run ruff format --check ."

# 3. MyPy - Type checking
run_check "MyPy (type checking)" "uv run mypy src/timeline_2_images"

# 4. PyLint - Advanced linting
run_check "PyLint" "uv run pylint src/timeline_2_images --exit-zero"

# 5. Radon - Complexity analysis
run_check "Radon (complexity)" "uv run radon cc src/timeline_2_images -a"

# 6. Radon - Maintainability index
run_check "Radon (maintainability)" "uv run radon mi src/timeline_2_images"

# 7. PyTest - Unit tests
run_check "PyTest (tests)" "uv run python -m pytest --tb=short"

# 8. PyTest - Coverage
run_check "PyTest (coverage)" "uv run python -m pytest --cov=src/timeline_2_images --cov-report=term-missing"

echo ""
echo "================================"
echo "Summary"
echo "================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Some checks failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
fi
