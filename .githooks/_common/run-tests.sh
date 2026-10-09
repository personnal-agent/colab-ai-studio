#!/usr/bin/env bash
# Exécution ciblée des tests unitaires pour Colab AI Studio
# Timeout : 5 minutes (300 secondes) pour préserver les ressources CPU/RAM

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TEST_TIMEOUT=300

echo -e "${BLUE}🧪 Recherche et exécution des suites de tests unitaires...${NC}"

TESTS_FOUND=0

# 1. Tests Python (FastAPI / services)
if find . -maxdepth 3 -type f \( -name 'test_*.py' -o -name '*_test.py' \) -print -quit | grep -q .; then
    TESTS_FOUND=1
    echo -e "${BLUE}  Exécution des tests Python (pytest)...${NC}"
    if command -v pytest >/dev/null 2>&1; then
        timeout $TEST_TIMEOUT pytest -q || {
            echo -e "${RED}❌ Échec de la suite de tests Python.${NC}"
            exit 1
        }
    else
        timeout $TEST_TIMEOUT python3 -m unittest discover -s tests -p "test_*.py" 2>/dev/null || {
            echo -e "${RED}❌ Échec des tests unitaires Python.${NC}"
            exit 1
        }
    fi
    echo -e "${GREEN}  ✓ Tests Python validés.${NC}"
fi

# 2. Tests Frontend (React)
if [ -f "frontend/package.json" ] && [ -d "frontend/node_modules" ]; then
    if grep -q '"test"' frontend/package.json; then
        TESTS_FOUND=1
        echo -e "${BLUE}  Exécution des tests Frontend (npm test)...${NC}"
        (cd frontend && timeout $TEST_TIMEOUT npm test -- --run) || {
            echo -e "${RED}❌ Échec de la suite de tests Frontend.${NC}"
            exit 1
        }
        echo -e "${GREEN}  ✓ Tests Frontend validés.${NC}"
    fi
fi

if [ $TESTS_FOUND -eq 0 ]; then
    echo -e "${YELLOW}  ℹ️  Aucune suite de tests active pour le moment (dépôt au stade de spécification).${NC}"
fi

exit 0
