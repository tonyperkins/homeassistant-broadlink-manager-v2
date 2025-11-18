#!/bin/bash
# Fix Docker 29.x on Home Assistant Supervised
# Run this on the Supervised host (not in a container)

set -e

echo "=========================================="
echo "Docker 29.x Fix for HA Supervised"
echo "=========================================="
echo ""

# Check current version
echo "Current Docker version:"
docker --version
echo ""

# Stop services
echo "Stopping Home Assistant services..."
ha core stop || true
sleep 5
systemctl stop hassio-supervisor || true
sleep 5

# Unhold packages if held
echo "Unholding Docker packages..."
sudo apt-mark unhold docker-ce docker-ce-cli || true

# Remove Docker 29.x
echo "Removing Docker 29.x..."
sudo apt-get remove -y --allow-change-held-packages docker-ce docker-ce-cli

# Install Docker 27.3.1
echo "Installing Docker 27.3.1..."
sudo apt-get install -y --allow-downgrades \
  docker-ce=5:27.3.1-1~debian.12~bookworm \
  docker-ce-cli=5:27.3.1-1~debian.12~bookworm \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# Hold version
echo "Holding Docker version to prevent auto-upgrade..."
sudo apt-mark hold docker-ce docker-ce-cli

# Restart Docker
echo "Restarting Docker..."
sudo systemctl restart docker
sleep 5

# Start Supervisor
echo "Starting Home Assistant Supervisor..."
systemctl start hassio-supervisor
sleep 10

echo ""
echo "=========================================="
echo "Fix Complete!"
echo "=========================================="
echo ""
echo "New Docker version:"
docker --version
echo ""
echo "Waiting 60 seconds for Supervisor to be ready..."
sleep 60

echo ""
echo "Testing Supervisor..."
ha supervisor info

echo ""
echo "You can now install add-ons:"
echo "  ha addons install 1ed199ed_broadlink-manager-v2"
echo "  ha addons start 1ed199ed_broadlink-manager-v2"
