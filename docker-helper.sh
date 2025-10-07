#!/bin/bash
# Convergio Docker Helper Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}🐳 Convergio Docker Helper${NC}"
    echo -e "${BLUE}=========================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_dependencies() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Docker dependencies are available"
}

check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f backend/.env.example ]; then
            cp backend/.env.example .env
            print_warning "Please edit .env file and add your API keys before starting services"
            return 1
        else
            print_error "No .env.example template found"
            exit 1
        fi
    fi
    print_success ".env file found"
    return 0
}

start_services() {
    print_header
    check_dependencies
    
    env_ok=0
    check_env_file || env_ok=$?
    
    if [ $env_ok -ne 0 ]; then
        echo
        print_warning "Please edit the .env file with your API keys and run this script again"
        exit 1
    fi
    
    echo
    echo -e "${BLUE}Starting Convergio services...${NC}"
    docker-compose up -d
    
    echo
    print_success "Services started! Waiting for health checks..."
    sleep 10
    
    echo
    echo -e "${BLUE}Service Status:${NC}"
    docker-compose ps
    
    echo
    echo -e "${BLUE}Access URLs:${NC}"
    echo "Frontend:  http://localhost:4000"
    echo "Backend:   http://localhost:9000"
    echo "API Docs:  http://localhost:9000/docs"
    echo "Health:    http://localhost:9000/health"
}

stop_services() {
    print_header
    echo -e "${BLUE}Stopping Convergio services...${NC}"
    docker-compose down
    print_success "Services stopped"
}

restart_services() {
    print_header
    echo -e "${BLUE}Restarting Convergio services...${NC}"
    docker-compose restart
    print_success "Services restarted"
}

view_logs() {
    service=${1:-""}
    if [ -z "$service" ]; then
        echo -e "${BLUE}Viewing all service logs (Ctrl+C to exit):${NC}"
        docker-compose logs -f
    else
        echo -e "${BLUE}Viewing logs for $service (Ctrl+C to exit):${NC}"
        docker-compose logs -f "$service"
    fi
}

show_status() {
    print_header
    echo -e "${BLUE}Service Status:${NC}"
    docker-compose ps
    
    echo
    echo -e "${BLUE}Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

cleanup() {
    print_header
    print_warning "This will remove all containers, networks, and volumes (including data!)"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Cleaning up Convergio deployment...${NC}"
        docker-compose down -v --remove-orphans
        print_success "Cleanup completed"
    else
        print_success "Cleanup cancelled"
    fi
}

show_help() {
    print_header
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  start              Start all services"
    echo "  stop               Stop all services"
    echo "  restart            Restart all services"
    echo "  status             Show service status and resource usage"
    echo "  logs [SERVICE]     View logs (all services or specific service)"
    echo "  cleanup            Remove all containers and data (⚠️  destructive)"
    echo "  help               Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start           # Start all services"
    echo "  $0 logs backend    # View backend logs"
    echo "  $0 logs            # View all logs"
    echo "  $0 status          # Check service status"
    echo
}

# Main script logic
case "${1:-}" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "logs")
        view_logs "${2:-}"
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        if [ -z "${1:-}" ]; then
            show_help
        else
            print_error "Unknown command: $1"
            echo
            show_help
            exit 1
        fi
        ;;
esac