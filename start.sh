#!/bin/bash
# =========================================================
# PRCI v2 — One-Command Startup Script
# Phase 4.4 — Full Production Deployment & Dockerization
#
# Usage:
#   chmod +x start.sh
#   ./start.sh          # Development mode
#   ./start.sh prod     # Production mode
#   ./start.sh down     # Stop all services
#   ./start.sh logs     # Follow logs
#   ./start.sh clean    # Stop & remove volumes
# =========================================================

set -e

MODE=${1:-dev}
COMPOSE_FILE="docker-compose.yml"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "============================================================"
    echo "  PRCI v2 — Mental Health Assessment & Intervention Platform"
    echo "============================================================"
    echo -e "${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed.${NC}"
        echo "Install from: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed.${NC}"
        echo "Install from: https://docs.docker.com/compose/install/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker daemon is not running.${NC}"
        exit 1
    fi
}

check_env() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Warning: .env file not found. Creating from template...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env and set real passwords before production use!${NC}"
    fi
}

dev_up() {
    print_banner
    echo -e "${GREEN}Starting PRCI v2 in DEVELOPMENT mode...${NC}"
    echo ""

    check_docker
    check_env

    echo -e "${BLUE}Building images and starting services...${NC}"
    docker compose -f $COMPOSE_FILE up --build -d

    echo ""
    echo -e "${GREEN}✅ All services started!${NC}"
    echo ""
    echo -e "  ${BLUE}Frontend:${NC}  http://localhost:8501"
    echo -e "  ${BLUE}Backend:${NC}   http://localhost:8000"
    echo -e "  ${BLUE}API Docs:${NC}  http://localhost:8000/docs"
    echo -e "  ${BLUE}Health:${NC}    http://localhost:8000/health"
    echo ""
    echo -e "  ${YELLOW}View logs:${NC}   ./start.sh logs"
    echo -e "  ${YELLOW}Stop:${NC}       ./start.sh down"
    echo ""
}

prod_up() {
    print_banner
    echo -e "${GREEN}Starting PRCI v2 in PRODUCTION mode...${NC}"
    echo ""

    check_docker
    check_env

    echo -e "${BLUE}Building images and starting services...${NC}"
    docker compose -f docker-compose.prod.yml up --build -d

    echo ""
    echo -e "${GREEN}✅ Production stack started!${NC}"
    echo ""
    echo -e "  ${BLUE}Nginx Proxy:${NC} http://localhost (or your domain)"
    echo -e "  ${BLUE}API:${NC}          http://localhost/api"
    echo -e "  ${BLUE}API Docs:${NC}     http://localhost/docs"
    echo ""
    echo -e "  ${YELLOW}View logs:${NC}   ./start.sh logs"
    echo -e "  ${YELLOW}Stop:${NC}       ./start.sh down"
    echo ""
}

down() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    docker compose -f docker-compose.yml down 2>/dev/null || true
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true
    echo -e "${GREEN}✅ All services stopped.${NC}"
}

clean() {
    echo -e "${RED}WARNING: This will remove all containers and volumes (database data will be lost)!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        docker compose -f docker-compose.yml down -v 2>/dev/null || true
        docker compose -f docker-compose.prod.yml down -v 2>/dev/null || true
        docker system prune -f
        echo -e "${GREEN}✅ Cleaned up everything.${NC}"
    else
        echo -e "${YELLOW}Cancelled.${NC}"
    fi
}

logs() {
    echo -e "${BLUE}Following logs (Ctrl+C to exit)...${NC}"
    docker compose -f docker-compose.yml logs -f 2>/dev/null || \
    docker compose -f docker-compose.prod.yml logs -f 2>/dev/null || \
    echo -e "${YELLOW}No running services found.${NC}"
}

health() {
    echo -e "${BLUE}Checking service health...${NC}"
    echo ""

    # Check nginx
    if curl -sf http://localhost/nginx-health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Nginx${NC}      — healthy"
    else
        echo -e "  ${RED}❌ Nginx${NC}      — unreachable"
    fi

    # Check backend
    if curl -sf http://localhost:8000/health/live > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Backend${NC}    — healthy"
    else
        echo -e "  ${RED}❌ Backend${NC}    — unreachable"
    fi

    # Check frontend
    if curl -sf http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Frontend${NC}   — healthy"
    else
        echo -e "  ${RED}❌ Frontend${NC}   — unreachable"
    fi

    # Check DB
    if docker compose -f docker-compose.yml exec -T db pg_isready -U prci > /dev/null 2>&1 || \
       docker compose -f docker-compose.prod.yml exec -T db pg_isready -U prci > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Database${NC}   — healthy"
    else
        echo -e "  ${RED}❌ Database${NC}   — unreachable"
    fi
}

# =========================================================
# Main
# =========================================================
case "$MODE" in
    dev|development|"")
        dev_up
        ;;
    prod|production)
        prod_up
        ;;
    down|stop)
        down
        ;;
    clean|reset)
        clean
        ;;
    logs)
        logs
        ;;
    health|status)
        health
        ;;
    *)
        echo "Usage: ./start.sh [dev|prod|down|clean|logs|health]"
        echo ""
        echo "  dev      — Start in development mode (default)"
        echo "  prod     — Start in production mode"
        echo "  down     — Stop all services"
        echo "  clean    — Stop and remove all data (⚠️ destructive)"
        echo "  logs     — Follow service logs"
        echo "  health   — Check service health status"
        exit 1
        ;;
esac
