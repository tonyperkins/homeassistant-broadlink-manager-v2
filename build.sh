#!/bin/bash

# Broadlink Manager Add-on Build Script
# This script helps build and deploy the add-on locally

set -e

echo "🏗️  Building Broadlink Manager Add-on..."

# Configuration
ADDON_NAME="broadlink-manager"
ADDON_DIR="/addons/local-addons/${ADDON_NAME}"
SOURCE_DIR="$(pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're running on Home Assistant OS
check_environment() {
    print_status "Checking environment..."
    
    if [ ! -d "/addons" ]; then
        print_error "This script should be run on Home Assistant OS or Supervised installation"
        print_error "The /addons directory was not found"
        exit 1
    fi
    
    print_success "Environment check passed"
}

# Create addon directory structure
create_addon_directory() {
    print_status "Creating add-on directory structure..."
    
    # Create the addon directory
    sudo mkdir -p "${ADDON_DIR}"
    
    # Set proper ownership
    sudo chown -R root:root "${ADDON_DIR}"
    
    print_success "Add-on directory created: ${ADDON_DIR}"
}

# Copy files to addon directory
copy_files() {
    print_status "Copying add-on files..."
    
    # Copy all necessary files
    sudo cp -r "${SOURCE_DIR}"/* "${ADDON_DIR}/"
    
    # Remove unnecessary files
    sudo rm -f "${ADDON_DIR}/build.sh"
    sudo rm -f "${ADDON_DIR}/DEPLOYMENT.md"
    sudo rm -rf "${ADDON_DIR}/reference"
    sudo rm -f "${ADDON_DIR}/prompt.txt"
    
    # Set executable permissions
    sudo chmod +x "${ADDON_DIR}/run.sh"
    
    # Set proper ownership
    sudo chown -R root:root "${ADDON_DIR}"
    
    print_success "Files copied successfully"
}

# Validate addon configuration
validate_config() {
    print_status "Validating add-on configuration..."
    
    # Check if required files exist
    required_files=("config.yaml" "Dockerfile" "run.sh" "requirements.txt" "app/main.py" "app/web_server.py")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "${ADDON_DIR}/${file}" ]; then
            print_error "Required file missing: ${file}"
            exit 1
        fi
    done
    
    print_success "Configuration validation passed"
}

# Main deployment function
deploy_addon() {
    print_status "Starting add-on deployment..."
    
    check_environment
    create_addon_directory
    copy_files
    validate_config
    
    print_success "Add-on deployed successfully!"
    echo ""
    print_status "Next steps:"
    echo "1. Open Home Assistant web interface"
    echo "2. Go to Settings → Add-ons"
    echo "3. Click 'Add-on Store'"
    echo "4. Click the three dots (⋮) and select 'Repositories'"
    echo "5. Add repository: /addons/local-addons"
    echo "6. Refresh and install 'Broadlink Manager'"
    echo ""
    print_status "The web interface will be available at: http://homeassistant.local:8099"
}

# Build Docker image locally (optional)
build_docker() {
    print_status "Building Docker image locally..."
    
    cd "${SOURCE_DIR}"
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)
            BUILD_ARCH="amd64"
            ;;
        aarch64)
            BUILD_ARCH="aarch64"
            ;;
        armv7l)
            BUILD_ARCH="armv7"
            ;;
        *)
            print_warning "Unknown architecture: $ARCH, defaulting to amd64"
            BUILD_ARCH="amd64"
            ;;
    esac
    
    print_status "Building for architecture: ${BUILD_ARCH}"
    
    docker build \
        --build-arg BUILD_FROM="ghcr.io/home-assistant/${BUILD_ARCH}-base:3.18" \
        -t "local/broadlink-manager:latest" \
        .
    
    print_success "Docker image built successfully"
}

# Show help
show_help() {
    echo "Broadlink Manager Add-on Build Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  deploy    Deploy the add-on to local Home Assistant (default)"
    echo "  build     Build Docker image locally"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy    # Deploy add-on to /addons/local-addons"
    echo "  $0 build     # Build Docker image"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        deploy_addon
        ;;
    "build")
        build_docker
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
