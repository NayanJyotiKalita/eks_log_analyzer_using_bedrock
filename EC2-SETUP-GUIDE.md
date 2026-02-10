# 🚀 Running EKS Analyzer on EC2

## Quick Start Guide

### Step 1: Create IAM Role for EC2

1. **Go to IAM Console** → Roles → Create Role
2. **Select trusted entity:** AWS service → EC2
3. **Create inline policy** using `ec2-iam-policy.json`:
   - Click "Create policy" → JSON tab
   - Paste contents of `ec2-iam-policy.json`
   - Name it: `EKSLogAnalyzerPolicy`
4. **Name the role:** `EKSLogAnalyzerRole`
5. **Create role**

### Step 2: Launch EC2 Instance

```bash
# Launch Amazon Linux 2 instance with the IAM role
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.small \
  --iam-instance-profile Name=EKSLogAnalyzerRole \
  --key-name YOUR-KEY-PAIR \
  --security-group-ids YOUR-SG-ID \
  --subnet-id YOUR-SUBNET-ID \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=EKS-Log-Analyzer}]'
```

Or use AWS Console:
1. EC2 → Launch Instance
2. **AMI:** Amazon Linux 2023 or Ubuntu
3. **Instance type:** t3.small (or t2.micro for testing)
4. **IAM role:** Select `EKSLogAnalyzerRole`
5. **Storage:** 8 GB is enough
6. **Launch**

### Step 3: Connect to EC2 and Setup

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@YOUR-EC2-IP

# Or use Session Manager (no SSH key needed)
aws ssm start-session --target INSTANCE-ID
```

### Step 4: Upload Project Files

**Option A: Using SCP**
```bash
# From your local machine
cd "/Users/raj/Documents/vilas class project/vilas vpc analyser"

# Upload files
scp -i your-key.pem -r ./* ec2-user@YOUR-EC2-IP:~/eks-log-analyzer/
```

**Option B: Using Git (if you push to GitHub)**
```bash
# On EC2
git clone https://github.com/your-repo/eks-log-analyzer.git
cd eks-log-analyzer
```

**Option C: Manual file transfer**
```bash
# On EC2, create files manually
mkdir -p ~/eks-log-analyzer
cd ~/eks-log-analyzer

# Then copy-paste the content of each file
nano eks_log_analyzer.py  # paste content
nano requirements.txt      # paste content
nano .env.example         # paste content
```

### Step 5: Install and Run

```bash
# On EC2 instance
cd ~/eks-log-analyzer

# Install dependencies
pip3 install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env  # Edit if needed (usually default is fine)

# Run the analyzer
python3 eks_log_analyzer.py
```

## 🔧 EC2 Instance Recommendations

### Minimum Requirements:
- **Type:** t3.micro or t2.micro
- **RAM:** 1 GB
- **Storage:** 8 GB
- **OS:** Amazon Linux 2023, Ubuntu 22.04, or Amazon Linux 2

### Recommended for Production:
- **Type:** t3.small
- **RAM:** 2 GB
- **Storage:** 20 GB
- **OS:** Amazon Linux 2023

## 🔐 Security Best Practices

### IAM Role (No Access Keys Needed!)
✅ Use IAM role attached to EC2
❌ Don't use access keys in `.env` file on EC2

### Security Group Rules
- **Inbound:** Only SSH (port 22) from your IP
- **Outbound:** Allow HTTPS (443) for AWS API calls

### Enable Session Manager (Optional)
- No need to open SSH port 22
- More secure than SSH
- Add `AmazonSSMManagedInstanceCore` policy to IAM role

## 🎯 Enable Bedrock Model Access

**IMPORTANT:** Still need to enable model access in Bedrock Console:

1. Go to AWS Bedrock Console
2. Click "Model access"
3. Enable "Claude 3 Sonnet"
4. Wait 2-3 minutes

## 💰 Cost Estimate

### EC2 Costs:
- **t3.micro:** ~$0.01/hour (~$7/month if running 24/7)
- **t2.micro:** ~$0.01/hour (free tier eligible)
- **Stop when not in use** to save costs

### Bedrock Costs:
- **Input:** ~$0.003 per 1K tokens
- **Output:** ~$0.015 per 1K tokens
- Typical query: $0.01 - $0.05

### CloudWatch Logs:
- **Ingestion:** $0.50 per GB
- **Storage:** $0.03 per GB per month

## 🚀 Quick Commands

```bash
# Start analyzer
python3 eks_log_analyzer.py

# Run in background (optional)
nohup python3 eks_log_analyzer.py > output.log 2>&1 &

# Check if running
ps aux | grep eks_log_analyzer

# Stop background process
pkill -f eks_log_analyzer.py
```

## 🐛 Troubleshooting

### Check IAM Role
```bash
# Verify IAM role is attached
aws sts get-caller-identity

# Should show assumed role, not IAM user
```

### Check Bedrock Access
```bash
# List available models
aws bedrock list-foundation-models --region us-east-1
```

### Check EKS Access
```bash
# List clusters
aws eks list-clusters --region us-east-1
```

## 📝 Advantages of EC2 Approach

✅ **No credential management** - Uses IAM role
✅ **Better security** - No access keys
✅ **Always available** - Run 24/7 if needed
✅ **Consistent environment** - Same setup every time
✅ **Easy to scale** - Can upgrade instance type
✅ **Cost effective** - Only pay for what you use
