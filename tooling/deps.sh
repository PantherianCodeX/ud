#!/usr/bin/env bash
# Dependency management helper script for uDocket monorepo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

usage() {
    cat << EOF
Usage: $0 <command> [options]

Dependency management helper for uDocket monorepo

Commands:
    check               Run dependency validation
    test                Run dependency checker tests
    sync                Sync all dependencies (uv sync)
    add <pkg> [target]  Add a dependency
    list [target]       List dependencies for a package/app
    help                Show this help message

Examples:
    $0 check                          # Validate all dependencies
    $0 test                           # Run validation tests
    $0 sync                           # Install all dependencies
    $0 add fastapi apps/api           # Add fastapi to the API app
    $0 add pytest                     # Add pytest to root (dev deps)
    $0 list apps/api                  # List API dependencies

Target can be:
    - Root workspace (default for dev deps)
    - packages/udocket_domain
    - packages/udocket_ai_core
    - packages/udocket_worker_core
    - apps/api
    - apps/celery
EOF
}

check_dependencies() {
    info "Running dependency validation..."
    cd "$ROOT_DIR"

    if uv run python tooling/check_dependencies.py; then
        success "All dependency checks passed!"
        return 0
    else
        error "Dependency validation failed!"
        echo ""
        warning "To fix issues, see: docs/DEPENDENCY_MANAGEMENT.md"
        return 1
    fi
}

test_checker() {
    info "Running dependency checker tests..."
    cd "$ROOT_DIR"

    if uv run pytest tooling/test_check_dependencies.py -v; then
        success "All tests passed!"
        return 0
    else
        error "Tests failed!"
        return 1
    fi
}

sync_deps() {
    info "Syncing dependencies with uv..."
    cd "$ROOT_DIR"

    if uv sync; then
        success "Dependencies synced successfully!"
        info "Running validation..."
        check_dependencies
        return 0
    else
        error "Failed to sync dependencies!"
        return 1
    fi
}

add_dependency() {
    local package="$1"
    local target="${2:-}"

    if [ -z "$package" ]; then
        error "Package name required!"
        echo "Usage: $0 add <package-name> [target]"
        return 1
    fi

    info "Adding dependency: $package"

    if [ -z "$target" ]; then
        warning "No target specified, adding to root workspace dev-dependencies"
        cd "$ROOT_DIR"
        if uv add --dev "$package"; then
            success "Added $package to root dev-dependencies"
        else
            error "Failed to add $package"
            return 1
        fi
    else
        if [ ! -d "$ROOT_DIR/$target" ]; then
            error "Target directory not found: $target"
            return 1
        fi

        cd "$ROOT_DIR/$target"
        if uv add "$package"; then
            success "Added $package to $target"
        else
            error "Failed to add $package to $target"
            return 1
        fi
    fi

    info "Running validation..."
    check_dependencies
}

list_dependencies() {
    local target="${1:-}"

    if [ -z "$target" ]; then
        info "Listing root workspace dependencies..."
        target="."
    else
        info "Listing dependencies for: $target"
    fi

    cd "$ROOT_DIR/$target"

    if [ ! -f "pyproject.toml" ]; then
        error "No pyproject.toml found in $target"
        return 1
    fi

    echo ""
    echo "Runtime dependencies:"
    echo "===================="
    uv pip list --format=columns | grep -v "^Package" | grep -v "^---" || echo "(none)"

    echo ""
    echo "Location: $target/pyproject.toml"
}

main() {
    local command="${1:-help}"

    case "$command" in
        check)
            check_dependencies
            ;;
        test)
            test_checker
            ;;
        sync)
            sync_deps
            ;;
        add)
            shift
            add_dependency "$@"
            ;;
        list)
            shift
            list_dependencies "$@"
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown command: $command"
            echo ""
            usage
            exit 1
            ;;
    esac
}

main "$@"
