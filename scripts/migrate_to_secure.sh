#!/bin/bash

# Script to migrate from hardcoded secrets to environment variables
# This script helps users transition to the secure docker-compose configuration

echo "🔒 CryptoBotDE Security Migration Script"
echo "======================================="
echo ""

# Check if .env file exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Copy from example if .env doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.example..."
    cp .env.example .env
fi

echo ""
echo "📝 Please edit the .env file and add your actual API keys and passwords:"
echo ""
echo "Required variables:"
echo "  - BINANCE_API_KEY"
echo "  - BINANCE_API_SECRET"
echo "  - DB_PASSWORD (change from default 'postgres')"
echo "  - AIRFLOW_DB_PASSWORD (change from default 'airflow')"
echo ""
echo "You can edit the file with: nano .env"
echo ""

# Ask if user wants to continue
read -p "Have you updated the .env file with your actual values? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled. Please update .env file and run this script again."
    exit 1
fi

# Backup old docker-compose.yml
echo "📦 Backing up original docker-compose.yml to docker-compose.yml.backup"
cp docker-compose.yml docker-compose.yml.backup

# Replace with secure version
echo "🔄 Replacing docker-compose.yml with secure version..."
cp docker-compose.secure.yml docker-compose.yml

echo ""
echo "✅ Migration completed!"
echo ""
echo "🚀 You can now start your services with:"
echo "   docker-compose up -d"
echo ""
echo "📌 Note: Your original docker-compose.yml has been backed up to docker-compose.yml.backup"
echo ""
echo "🔐 Security improvements applied:"
echo "   ✓ All secrets now read from environment variables"
echo "   ✓ Health checks added to all services"
echo "   ✓ Database passwords can be customized"
echo "   ✓ No hardcoded API keys in configuration files" 