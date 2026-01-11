#!/bin/bash
# EC2 Ubuntu Setup Script for arXiv Vector Search
# Run this script once on a fresh Ubuntu EC2 instance
#
# Usage:
#   chmod +x scripts/ec2-setup.sh
#   ./scripts/ec2-setup.sh
#
# Prerequisites:
#   - Ubuntu EC2 instance (t3.medium or larger recommended)
#   - At least 20GB EBS storage
#   - Security group with ports 22, 80, 8000 open

set -e  # Exit on any error

echo "=== arXiv Vector Search - EC2 Setup ==="
echo ""

# Update system
echo ">>> Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
echo ">>> Installing Docker..."
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group
echo ">>> Adding user to docker group..."
sudo usermod -aG docker $USER

# Verify installation
echo ">>> Verifying Docker installation..."
docker --version
docker compose version

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ">>> Creating .env file..."

    # Try to get public IP
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")

    if [ -z "$PUBLIC_IP" ]; then
        echo "Could not detect public IP. Please edit .env manually."
        PUBLIC_IP="YOUR_EC2_PUBLIC_IP"
    fi

    cat > .env << EOF
# EC2 Configuration
# Replace YOUR_EC2_PUBLIC_IP with your actual EC2 public IP if not auto-detected
CORS_ORIGINS=http://${PUBLIC_IP},http://${PUBLIC_IP}:80,http://localhost
VITE_API_URL=http://${PUBLIC_IP}:8000
EOF

    echo "Created .env file with IP: ${PUBLIC_IP}"
    echo "Please verify the .env file contents:"
    cat .env
else
    echo ">>> .env file already exists, skipping..."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Log out and log back in (for docker group to take effect), or run: newgrp docker"
echo "2. Verify .env file has correct IP: cat .env"
echo "3. Start the application: docker compose -f docker-compose.prod.yml up -d --build"
echo "4. Check status: docker compose -f docker-compose.prod.yml ps"
echo "5. View logs: docker compose -f docker-compose.prod.yml logs -f"
echo "6. Test health: curl http://localhost:8000/health"
echo ""
