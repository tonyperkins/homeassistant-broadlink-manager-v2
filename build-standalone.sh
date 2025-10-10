#!/bin/bash
# Build script for Broadlink Manager standalone Docker image

set -e

echo "=========================================="
echo "Building Broadlink Manager Standalone"
echo "=========================================="

# Get version from config.yaml and strip Windows line endings
VERSION=$(grep "^version:" config.yaml | awk '{print $2}' | tr -d '"\r')
echo "Version: $VERSION"

# Image name
IMAGE_NAME="broadlink-manager"
TAG="${VERSION}-standalone"

echo ""
echo "Building Docker image..."
echo "Image: ${IMAGE_NAME}:${TAG}"
echo ""

# Build the image
docker build \
  -f Dockerfile.standalone \
  -t "${IMAGE_NAME}:${TAG}" \
  -t "${IMAGE_NAME}:standalone" \
  -t "${IMAGE_NAME}:latest-standalone" \
  .

echo ""
echo "=========================================="
echo "Build complete!"
echo "=========================================="
echo ""
echo "Tagged as:"
echo "  - ${IMAGE_NAME}:${TAG}"
echo "  - ${IMAGE_NAME}:standalone"
echo "  - ${IMAGE_NAME}:latest-standalone"
echo ""
echo "To run:"
echo "  docker-compose up -d"
echo ""
echo "Or manually:"
echo "  docker run -d \\"
echo "    --name broadlink-manager \\"
echo "    --network host \\"
echo "    -e HA_URL=http://localhost:8123 \\"
echo "    -e HA_TOKEN=your_token_here \\"
echo "    -v /path/to/ha/config:/config \\"
echo "    ${IMAGE_NAME}:standalone"
echo ""
