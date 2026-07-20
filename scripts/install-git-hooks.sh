#!/usr/bin/env bash
# Install git hooks for this project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.githooks"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Installing git hooks...${NC}"
echo ""

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Make hook scripts executable
chmod +x "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/post-commit"

# Configure git to use .githooks directory
git config core.hooksPath .githooks

echo -e "${GREEN}✓ Configured git to use .githooks${NC}"
echo -e "${GREEN}✓ Made hook scripts executable${NC}"
echo ""

echo "Git hooks installed:"
echo -e "  ${YELLOW}pre-commit${NC}  - Validates version consistency + ruff checks"
echo -e "    • Version consistency across __init__.py, pyproject.toml, .bumpversion.cfg"
echo -e "    • Ruff linting (informational, doesn't block commit)"
echo -e "    • Ruff formatting check (informational, doesn't block commit)"
echo -e "  ${YELLOW}post-commit${NC} - Suggests version bumping"
echo ""

echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "Next time you commit, the hooks will run automatically."
echo ""
echo "To test the hooks:"
echo -e "  ${CYAN}cd $PROJECT_ROOT && git commit --allow-empty -m 'Test commit'${NC}"
echo ""
echo "To uninstall hooks:"
echo -e "  ${CYAN}git config --unset core.hooksPath${NC}"
