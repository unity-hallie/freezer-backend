#!/bin/bash
# One-click deployment script for Linode/DigitalOcean droplet
# Run this on your $6/month server!

set -e

echo "🚀 Freezer App Droplet Deployment"
echo "=================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Don't run this script as root. Use a sudo user instead."
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
echo "🐳 Installing Docker..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Install other tools
echo "🛠️ Installing additional tools..."
sudo apt install -y git nginx-utils netcat-openbsd

# Clone repositories (you'll need to update these URLs)
echo "📥 Cloning repositories..."
git clone https://github.com/yourusername/freezer-backend.git
git clone https://github.com/yourusername/freezer-frontend.git

# Build frontend
echo "🏗️ Building frontend..."
cd freezer-frontend
npm install
npm run build
cd ..

# Set up environment
echo "🔧 Setting up environment..."
cd freezer-backend
cp .env.droplet .env

# Generate secure passwords
echo "🔐 Generating secure secrets..."
DB_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")

# Update .env file
sed -i "s/your-secure-database-password-here/$DB_PASSWORD/" .env
sed -i "s/your-secure-jwt-secret-key-64-chars-minimum/$JWT_SECRET/" .env

echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Update your domain DNS to point to this server IP"
echo "2. Update CORS_ORIGINS in .env with your actual domain"
echo "3. Run: docker compose restart api"
echo "4. Set up SSL: docker compose run --rm certbot"
echo ""
echo "💰 Monthly cost: ~$6 (Linode Nanode 1GB)"
echo "🌐 Your API will be available at: https://your-domain.com/api/"
echo ""