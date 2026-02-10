# 🔍 AWS Bedrock EKS Log Analyzer

An intelligent EKS (Elastic Kubernetes Service) cluster log analyzer that uses AWS Bedrock to answer natural language questions about your Kubernetes cluster activities.

## 🎯 Features

- ✅ Validates EKS cluster existence
- 🔍 Checks EKS cluster logging status
- 📊 Retrieves and analyzes detailed cluster logs (API, Audit, Authenticator, etc.)
- 🤖 Natural language queries using AWS Bedrock (Claude 3 Sonnet)
- 📈 Access to actual log records with timestamps
- 🎯 Specific answers about API requests, authentication, pod activities
- ⏰ Custom time range selection
- 🔐 Security and anomaly detection

## 📋 Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Python 3.8+**
3. **AWS Bedrock access** in your region
4. **EKS cluster** with logging enabled
5. **CloudWatch Logs** enabled for your EKS cluster

## 🔑 Required AWS Permissions

Your AWS credentials need the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "logs:DescribeLogGroups",
        "logs:FilterLogEvents",
        "logs:DescribeLogStreams",
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

### Bedrock-Specific Requirements

1. **Model Access**: Ensure Claude 3 Sonnet is enabled in your AWS region
   - Go to AWS Bedrock Console → Model Access
   - Request access to `anthropic.claude-3-sonnet-20240229-v1:0`

2. **Regional Availability**: Bedrock is available in limited regions:
   - `us-east-1` (N. Virginia) - Recommended
   - `us-west-2` (Oregon)
   - `eu-west-1` (Ireland)

3. **No Additional Setup**: No need to create agents, knowledge bases, or other Bedrock resources

## 🚀 Installation

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Copy environment configuration:**
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` with your preferred settings**

## 📖 Usage

Run the analyzer:

```bash
python eks_log_analyzer.py
```

The tool will:
1. List all EKS clusters in your region
2. Ask for your EKS cluster name
3. Check if the cluster exists
4. Verify cluster logging is enabled
5. Ask for the time range (hours of logs to analyze)
6. Retrieve and analyze cluster logs for the specified period
7. Allow you to ask natural language questions

## 💬 Example Questions

The analyzer has access to detailed EKS cluster logs and can answer specific questions:

### API Server Analysis:
- "What API requests do you see?"
- "Show me all API calls to the kube-apiserver"
- "Which endpoints were accessed most frequently?"

### Authentication & Authorization:
- "Show me authentication failures"
- "Which users accessed the cluster?"
- "Are there any unauthorized access attempts?"

### Pod & Deployment Activities:
- "What pods were created or deleted?"
- "Show me all pod scheduling events"
- "Which namespaces had the most activity?"

### Security Analysis:
- "Show me suspicious activities"
- "Are there any security warnings or errors?"
- "Which service accounts were used?"

### Error & Troubleshooting:
- "Show me all errors in the logs"
- "What warnings do you see?"
- "Are there any failed operations?"

### Audit Trail:
- "Who made changes to the cluster?"
- "What RBAC actions were performed?"
- "Show me cluster configuration changes"

## ⚙️ Configuration

Edit `.env` file to customize:

- `AWS_REGION`: Your AWS region (default: us-east-1)
- `BEDROCK_MODEL_ID`: Bedrock model to use
- `DEFAULT_HOURS_BACK`: Default hours of logs to analyze (default: 24)
- `MAX_LOG_ENTRIES`: Maximum log entries to process (default: 1000)
- `EKS_LOG_TYPES`: Log types to analyze (api, audit, authenticator, controllerManager, scheduler)

## 🔧 EKS Logging Configuration

### Enable EKS Cluster Logging

If your cluster doesn't have logging enabled, you can enable it:

**Using AWS Console:**
1. Go to Amazon EKS Console
2. Select your cluster
3. Go to 'Observability' tab
4. Click 'Manage logging'
5. Enable desired log types:
   - **API server** - Kubernetes API requests
   - **Audit** - Audit trail of API requests
   - **Authenticator** - Authentication logs
   - **Controller Manager** - Cluster state management
   - **Scheduler** - Pod scheduling decisions
6. Click 'Save changes'

**Using AWS CLI:**
```bash
aws eks update-cluster-config \
  --region us-east-1 \
  --name your-cluster-name \
  --logging '{
    "clusterLogging":[{
      "types":["api","audit","authenticator","controllerManager","scheduler"],
      "enabled":true
    }]
  }'
```

**⏰ Note**: After enabling, wait 5-10 minutes for logs to start appearing in CloudWatch.

## 🐛 Troubleshooting

### EKS Cluster Not Found
- Verify the cluster name is correct
- Check you're in the correct AWS region
- Ensure your AWS credentials have `eks:DescribeCluster` permission

### EKS Logging Not Enabled
The tool provides step-by-step instructions to enable EKS cluster logging if it's not already configured.

### No Log Data Found
- Wait 10-15 minutes after enabling cluster logging
- Verify there's actual cluster activity
- Check if logs are being sent to CloudWatch (not S3)

### Bedrock Access Issues

**Model Access Denied:**
```
AccessDeniedException: You don't have access to the model with the specified model ID.
```
- **Solution**: Request access to Claude 3 Sonnet in Bedrock Console → Model Access
- **Wait Time**: Model access approval can take a few minutes

**Region Not Supported:**
```
ValidationException: Bedrock is not supported in this region
```
- **Solution**: Use a supported region (us-east-1, us-west-2, eu-west-1)
- **Update**: Change `AWS_REGION` in your `.env` file

**Token Limit Exceeded:**
```
ValidationException: Input is too long
```
- **Cause**: Too much log data sent to Bedrock
- **Solution**: Tool automatically limits to 150 records
- **Workaround**: Reduce the time range (use fewer hours)

## 🏗️ Architecture

The analyzer consists of:

- **EKSLogAnalyzer**: Main class handling AWS interactions
- **Log Retriever**: Fetches logs from CloudWatch for specific log types
- **Bedrock Runtime Integration**: Direct model invocation for natural language processing
- **Data Formatter**: Converts EKS logs to Bedrock-optimized format
- **Interactive Q&A**: Real-time question-answer interface

### Log Types Analyzed

| Log Type | Description | Use Case |
|----------|-------------|----------|
| **api** | Kubernetes API server logs | API requests, resource access |
| **audit** | Audit logs of API requests | Security, compliance, who did what |
| **authenticator** | AWS IAM Authenticator logs | Authentication attempts, user access |
| **controllerManager** | Controller manager logs | Cluster state, reconciliation |
| **scheduler** | Scheduler logs | Pod scheduling decisions |

```.env`` The file is added to the GitHub account because it does not contain any secrets but variables to run the code.

## 🔐 AWS Bedrock Integration Details

### How Bedrock is Utilized

This tool uses **AWS Bedrock Runtime API** (not Bedrock Agents) to provide intelligent analysis of EKS cluster logs.

#### Bedrock Model Used
- **Model**: `anthropic.claude-3-sonnet-20240229-v1:0` (Claude 3 Sonnet)
- **API**: `bedrock-runtime` client with `invoke_model` method
- **No Bedrock Resources Created**: Stateless implementation

#### Data Processing Flow

1. **Log Retrieval**: Fetches raw EKS logs from CloudWatch Logs
2. **Data Formatting**: Converts logs into structured, readable format with timestamps
3. **Context Creation**: Builds comprehensive system prompt with:
   - Summary statistics (total events, log types)
   - Detailed log records (up to 150 records)
   - Specific instructions for Kubernetes/EKS analysis
4. **Bedrock Query**: Sends formatted data and user question to Claude 3 Sonnet
5. **Response Processing**: Returns AI-generated analysis

#### Token Management
- **Limit**: Up to 150 log records per query to avoid token limits
- **Max Tokens**: 2000 tokens for responses
- **Optimization**: Compact format reduces token usage while preserving detail

#### Cost Considerations
- **Pay-per-use**: Only charged for actual model invocations
- **Input Tokens**: Based on log data size + system prompt
- **Output Tokens**: Based on response length (max 2000 tokens)
- **No Setup Costs**: No infrastructure or agent setup required

## 🆚 Differences from VPC Flow Log Analyzer

| Aspect | VPC Flow Logs | EKS Cluster Logs |
|--------|---------------|------------------|
| **Data Source** | Network traffic flow | Kubernetes control plane logs |
| **Log Format** | IP, port, protocol, bytes | API requests, audit events, authentication |
| **Analysis Focus** | Network security, traffic patterns | Cluster operations, security, user actions |
| **Use Cases** | Firewall rules, network troubleshooting | K8s debugging, security audits, compliance |
| **Log Types** | Single flow log format | Multiple types (api, audit, authenticator, etc.) |

## 📚 Additional Resources

- [Amazon EKS Documentation](https://docs.aws.amazon.com/eks/)
- [EKS Cluster Logging](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Kubernetes Audit Logs](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## ⚠️ Important Notes

1. **Costs**: This tool makes API calls to AWS Bedrock, which incurs costs. Monitor your usage.
2. **Security**: Never commit your `.env` file with AWS credentials to version control.
3. **Logging**: Keep cluster logging enabled only when needed to reduce CloudWatch costs.
4. **Data Privacy**: Be cautious when sharing log analysis outputs, as they may contain sensitive information.

---

**Built with ❤️ for Kubernetes administrators and DevOps engineers**
