#!/bin/bash

# EC2 Setup Script for EKS Log Analyzer
# Run this script on your EC2 instance after launch

set -e

echo "🚀 Setting up EKS Log Analyzer on EC2..."

# Update system
echo "📦 Updating system packages..."
sudo yum update -y || sudo apt-get update -y

# Install Python 3 and git
echo "🐍 Installing Python 3 and dependencies..."
sudo yum install -y python3 python3-pip git || sudo apt-get install -y python3 python3-pip git

# Install AWS CLI if not present
if ! command -v aws &> /dev/null; then
    echo "📥 Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Create project directory
echo "📁 Creating project directory..."
mkdir -p ~/eks-log-analyzer
cd ~/eks-log-analyzer

# Copy files (you'll upload these)
echo "📋 Ready to receive project files..."
echo ""
echo "Next steps:"
echo "1. Upload your project files to this EC2 instance"
echo "2. Run: cd ~/eks-log-analyzer"
echo "3. Run: pip3 install -r requirements.txt"
echo "4. Run: cp .env.example .env"
echo "5. Run: python3 eks_log_analyzer.py"

echo ""
echo "✅ EC2 setup complete!"
