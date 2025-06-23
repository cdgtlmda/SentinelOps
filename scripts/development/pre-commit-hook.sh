#!/bin/bash

# Pre-commit hook for SentinelOps
# Ensures code compliance before allowing commits

# Set colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== SentinelOps Pre-Commit Check ===${NC}"

# Get list of staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    echo -e "${GREEN}No Python files to check.${NC}"
    exit 0
fi

echo -e "${BLUE}Checking ${#STAGED_FILES[@]} staged Python files...${NC}"
echo ""

# Track if any checks fail
FAILED=0
FIXED_FILES=""

# Check each staged file
for FILE in $STAGED_FILES; do
    echo -e "${BLUE}Checking: $FILE${NC}"
    
    # Skip if file doesn't exist (deleted)
    if [ ! -f "$FILE" ]; then
        continue
    fi
    
    # Auto-format with black (if available)
    if command -v black &> /dev/null; then
        echo -n "  Auto-formatting... "
        if black "$FILE" --quiet 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
            # Check if black made changes
            if ! git diff --quiet "$FILE"; then
                FIXED_FILES="$FIXED_FILES $FILE"
            fi
        else
            echo -e "${RED}✗${NC}"
        fi
    fi
    
    # Sort imports with isort (if available)
    if command -v isort &> /dev/null; then
        echo -n "  Sorting imports... "
        if isort "$FILE" --quiet 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
            # Check if isort made changes
            if ! git diff --quiet "$FILE"; then
                FIXED_FILES="$FIXED_FILES $FILE"
            fi
        else
            echo -e "${RED}✗${NC}"
        fi
    fi
    
    # Type checking with mypy
    echo -n "  Type checking... "
    if mypy "$FILE" --ignore-missing-imports --no-error-summary > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo -e "${YELLOW}    Run 'mypy $FILE' to see errors${NC}"
        FAILED=1
    fi
    
    # Security check for high severity issues only
    echo -n "  Security check... "
    BANDIT_OUTPUT=$(bandit "$FILE" -lll -f json 2>/dev/null)
    if [ -z "$BANDIT_OUTPUT" ] || [ "$BANDIT_OUTPUT" == "[]" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo -e "${RED}    High severity security issues found!${NC}"
        bandit "$FILE" -lll
        FAILED=1
    fi
    
    # Basic style check
    echo -n "  Style check... "
    if flake8 "$FILE" --max-line-length=100 --extend-ignore=E203,W503 --count --quiet > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠${NC}"
        STYLE_ERRORS=$(flake8 "$FILE" --max-line-length=100 --extend-ignore=E203,W503 --count 2>/dev/null | tail -1)
        echo -e "${YELLOW}    $STYLE_ERRORS style issues (non-blocking)${NC}"
    fi
    
    # Check for print statements (excluding scripts)
    if [[ "$FILE" != scripts/* ]] && [[ "$FILE" != */main.py ]]; then
        echo -n "  No print statements... "
        if ! grep -n "print(" "$FILE" | grep -v "# noqa" > /dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠${NC}"
            echo -e "${YELLOW}    Found print statements - use logging instead${NC}"
        fi
    fi
    
    echo ""
done

# If files were auto-fixed, notify user
if [ -n "$FIXED_FILES" ]; then
    echo -e "${YELLOW}=========================================${NC}"
    echo -e "${YELLOW}Files were auto-formatted:${NC}"
    for FILE in $FIXED_FILES; do
        echo -e "${YELLOW}  - $FILE${NC}"
    done
    echo -e "${YELLOW}Please review and stage the changes:${NC}"
    echo -e "${GREEN}  git add $FIXED_FILES${NC}"
    echo -e "${YELLOW}=========================================${NC}"
    FAILED=1
fi

# Summary
echo -e "${BLUE}=========================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo -e "${GREEN}Commit approved.${NC}"
else
    echo -e "${RED}❌ Pre-commit checks failed!${NC}"
    echo -e "${RED}Please fix the issues above before committing.${NC}"
    echo ""
    echo -e "${YELLOW}To bypass (not recommended):${NC}"
    echo -e "${YELLOW}  git commit --no-verify${NC}"
fi
echo -e "${BLUE}=========================================${NC}"

exit $FAILED
