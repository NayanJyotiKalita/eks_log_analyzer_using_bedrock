#!/usr/bin/env python3
"""
EKS Log Analyzer with AWS Bedrock Integration
Analyzes EKS cluster logs using natural language queries powered by AWS Bedrock
"""

import boto3
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()


class EKSLogAnalyzer:
    """Main class for analyzing EKS cluster logs using AWS Bedrock"""
    
    def __init__(self, region_name: str = None):
        """Initialize the EKS Log Analyzer"""
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-2')
        self.model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
        self.max_log_entries = int(os.getenv('MAX_LOG_ENTRIES', 1000))
        
        # Initialize AWS clients
        self.eks_client = boto3.client('eks', region_name=self.region_name)
        self.logs_client = boto3.client('logs', region_name=self.region_name)
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region_name)
        
        print(f"✅ Initialized EKS Log Analyzer in region: {self.region_name}")
    
    def list_clusters(self) -> List[str]:
        """List all EKS clusters in the region"""
        try:
            response = self.eks_client.list_clusters()
            clusters = response.get('clusters', [])
            return clusters
        except Exception as e:
            print(f"❌ Error listing clusters: {str(e)}")
            return []
    
    def check_cluster_exists(self, cluster_name: str) -> bool:
        """Check if an EKS cluster exists"""
        try:
            self.eks_client.describe_cluster(name=cluster_name)
            print(f"✅ Cluster '{cluster_name}' found!")
            return True
        except self.eks_client.exceptions.ResourceNotFoundException:
            print(f"❌ Cluster '{cluster_name}' not found in region {self.region_name}")
            return False
        except Exception as e:
            print(f"❌ Error checking cluster: {str(e)}")
            return False
    
    def get_cluster_logging_config(self, cluster_name: str) -> Dict:
        """Get the logging configuration for an EKS cluster"""
        try:
            response = self.eks_client.describe_cluster(name=cluster_name)
            logging_config = response['cluster'].get('logging', {})
            return logging_config
        except Exception as e:
            print(f"❌ Error getting logging config: {str(e)}")
            return {}
    
    def check_cluster_logging(self, cluster_name: str) -> tuple[bool, List[str]]:
        """Check if cluster logging is enabled and return enabled log types"""
        logging_config = self.get_cluster_logging_config(cluster_name)
        
        cluster_logging = logging_config.get('clusterLogging', [])
        enabled_types = []
        
        for log_config in cluster_logging:
            if log_config.get('enabled', False):
                enabled_types.extend(log_config.get('types', []))
        
        if enabled_types:
            print(f"✅ Cluster logging is enabled!")
            print(f"   Enabled log types: {', '.join(enabled_types)}")
            return True, enabled_types
        else:
            print(f"❌ Cluster logging is NOT enabled for '{cluster_name}'")
            self._print_enable_logging_instructions(cluster_name)
            return False, []
    
    def _print_enable_logging_instructions(self, cluster_name: str):
        """Print instructions to enable EKS cluster logging"""
        print("\n📋 To enable EKS cluster logging:")
        print("\n1. Using AWS Console:")
        print("   - Go to Amazon EKS Console")
        print(f"   - Select cluster: {cluster_name}")
        print("   - Go to 'Observability' tab")
        print("   - Click 'Manage logging'")
        print("   - Enable desired log types (api, audit, authenticator, controllerManager, scheduler)")
        print("   - Click 'Save changes'")
        
        print("\n2. Using AWS CLI:")
        print(f"   aws eks update-cluster-config \\")
        print(f"     --region {self.region_name} \\")
        print(f"     --name {cluster_name} \\")
        print(f"     --logging '{{")
        print(f'       "clusterLogging":[{{')
        print(f'         "types":["api","audit","authenticator","controllerManager","scheduler"],')
        print(f'         "enabled":true')
        print(f"       }}]")
        print(f"     }}'")
        
        print("\n⏰ Note: After enabling, wait 5-10 minutes for logs to start appearing.")
    
    def get_log_group_name(self, cluster_name: str) -> str:
        """Get the CloudWatch log group name for an EKS cluster"""
        return f"/aws/eks/{cluster_name}/cluster"
    
    def get_log_streams(self, cluster_name: str, log_type: str) -> List[str]:
        """Get log streams for a specific log type"""
        log_group = self.get_log_group_name(cluster_name)
        
        try:
            # Note: Cannot use orderBy with logStreamNamePrefix, so we get all and sort manually
            response = self.logs_client.describe_log_streams(
                logGroupName=log_group,
                logStreamNamePrefix=log_type,
                limit=50
            )
            streams_data = response.get('logStreams', [])
            # Sort by last event time (most recent first)
            sorted_streams = sorted(streams_data, key=lambda x: x.get('lastEventTimestamp', 0), reverse=True)
            streams = [stream['logStreamName'] for stream in sorted_streams[:5]]
            return streams
        except self.logs_client.exceptions.ResourceNotFoundException:
            print(f"⚠️  Log group not found: {log_group}")
            return []
        except Exception as e:
            print(f"❌ Error getting log streams: {str(e)}")
            return []
    
    def retrieve_logs(self, cluster_name: str, hours_back: int = 24, log_types: List[str] = None) -> List[Dict]:
        """Retrieve EKS cluster logs from CloudWatch"""
        log_group = self.get_log_group_name(cluster_name)
        
        # Calculate time range
        end_time = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        print(f"\n🔍 Retrieving logs from {start_time.strftime('%Y-%m-%d %H:%M:%S')} to {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_log_events = []
        
        # If no log types specified, try to get all enabled types
        if not log_types:
            _, enabled_types = self.check_cluster_logging(cluster_name)
            log_types = enabled_types if enabled_types else ['api', 'audit']
        
        for log_type in log_types:
            try:
                print(f"   📥 Fetching {log_type} logs...")
                
                # Get log streams for this type
                streams = self.get_log_streams(cluster_name, log_type)
                
                if not streams:
                    print(f"   ⚠️  No log streams found for {log_type}")
                    continue
                
                # Fetch logs from each stream
                for stream in streams[:3]:  # Limit to top 3 streams per type
                    try:
                        response = self.logs_client.filter_log_events(
                            logGroupName=log_group,
                            logStreamNames=[stream],
                            startTime=start_timestamp,
                            endTime=end_timestamp,
                            limit=self.max_log_entries // len(log_types)
                        )
                        
                        events = response.get('events', [])
                        for event in events:
                            event['logType'] = log_type
                            all_log_events.append(event)
                        
                        print(f"      ✓ Retrieved {len(events)} events from {stream}")
                        
                    except Exception as e:
                        print(f"      ⚠️  Error fetching from stream {stream}: {str(e)}")
                        continue
                
            except Exception as e:
                print(f"   ❌ Error fetching {log_type} logs: {str(e)}")
                continue
        
        print(f"\n✅ Total log events retrieved: {len(all_log_events)}")
        return all_log_events
    
    def format_logs_for_bedrock(self, log_events: List[Dict], hours_back: int) -> str:
        """Format log events into a readable format for Bedrock analysis"""
        if not log_events:
            return "No log events found in the specified time range."
        
        # Sort by timestamp
        sorted_logs = sorted(log_events, key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Limit to prevent token overflow (150 most recent events)
        limited_logs = sorted_logs[:150]
        
        # Create summary statistics
        total_events = len(log_events)
        log_types = {}
        
        for event in log_events:
            log_type = event.get('logType', 'unknown')
            log_types[log_type] = log_types.get(log_type, 0) + 1
        
        # Build formatted output
        formatted = f"=== EKS CLUSTER LOGS ANALYSIS ===\n"
        formatted += f"Time Range: Last {hours_back} hours\n"
        formatted += f"Total Events: {total_events}\n"
        formatted += f"Log Types: {', '.join([f'{k}({v})' for k, v in log_types.items()])}\n"
        formatted += f"\n=== DETAILED LOG EVENTS (Most Recent {len(limited_logs)}) ===\n\n"
        
        for idx, event in enumerate(limited_logs, 1):
            timestamp = datetime.fromtimestamp(event.get('timestamp', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S')
            log_type = event.get('logType', 'unknown')
            message = event.get('message', '').strip()
            
            formatted += f"{idx}. [{timestamp}] [{log_type.upper()}]\n"
            formatted += f"   {message[:500]}...\n\n" if len(message) > 500 else f"   {message}\n\n"
        
        return formatted
    
    def ask_bedrock(self, context: str, question: str) -> str:
        """Send a question to AWS Bedrock with log context"""
        system_prompt = f"""You are an expert Kubernetes and EKS cluster analyst. You have access to EKS cluster logs and can answer detailed questions about cluster activities, API requests, authentication, pod scheduling, and security events.

{context}

Provide specific, detailed answers based on the actual log data above. Reference specific timestamps, log types, and events in your responses. If you see patterns or anomalies, point them out."""

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.1,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            answer = response_body['content'][0]['text']
            return answer
            
        except Exception as e:
            return f"❌ Error calling Bedrock: {str(e)}\n\nMake sure you have:\n1. Enabled Claude 3 Sonnet in Bedrock Console\n2. Correct AWS credentials with bedrock:InvokeModel permission\n3. Using a supported region (us-east-1, us-west-2, eu-west-1)"
    
    def ask_general_eks_question(self, question: str, cluster_name: str = None) -> str:
        """Ask general EKS questions without log context"""
        
        # Check if user is asking about their actual AWS resources
        question_lower = question.lower()
        if any(keyword in question_lower for keyword in ['my cluster', 'my eks', 'how many cluster', 'list cluster', 'number of cluster']):
            # Fetch actual AWS data
            clusters = self.list_clusters()
            aws_data = f"\n\n=== USER'S ACTUAL AWS RESOURCES ===\n"
            aws_data += f"Region: {self.region_name}\n"
            aws_data += f"Number of EKS Clusters: {len(clusters)}\n"
            if clusters:
                aws_data += f"Cluster Names: {', '.join(clusters)}\n"
            else:
                aws_data += "No EKS clusters found in this region.\n"
        else:
            aws_data = ""
        
        context = f"""You are an expert on Amazon EKS (Elastic Kubernetes Service) and Kubernetes. 
You help users understand EKS concepts, troubleshoot issues, and provide best practices.
"""
        if cluster_name:
            context += f"\nThe user is working with EKS cluster: {cluster_name}"
        
        if aws_data:
            context += aws_data
            context += "\nWhen asked about the user's clusters, use the ACTUAL AWS data provided above."
        
        context += """

Provide detailed, practical answers about:
- EKS architecture and components
- Kubernetes concepts and operations
- Troubleshooting and debugging
- Security and IAM
- Networking and service mesh
- Best practices and recommendations
- AWS-specific Kubernetes features"""

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 3000,
            "temperature": 0.3,
            "system": context,
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            answer = response_body['content'][0]['text']
            return answer
            
        except Exception as e:
            return f"❌ Error calling Bedrock: {str(e)}"
    
    def interactive_general_mode(self, cluster_name: str = None):
        """Interactive Q&A for general EKS questions"""
        print("\n" + "="*80)
        print("🤖 EKS KNOWLEDGE ASSISTANT")
        print("="*80)
        print("\nAsk me anything about EKS and Kubernetes!")
        print("\nExample questions:")
        print("  • How do I troubleshoot pod crashes in EKS?")
        print("  • What's the difference between EKS node groups and Fargate?")
        print("  • How do I set up IRSA (IAM Roles for Service Accounts)?")
        print("  • What are EKS best practices for security?")
        print("  • How do I configure cluster autoscaling?")
        print("  • Explain EKS networking and VPC CNI")
        print("  • How do I upgrade my EKS cluster version?")
        print("\nType 'exit' or 'quit' to end the session.\n")
        
        while True:
            try:
                question = input("\n🔍 Your question: ").strip()
                
                if question.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if not question:
                    continue
                
                print("\n🤔 Thinking...")
                answer = self.ask_general_eks_question(question, cluster_name)
                print(f"\n💡 Answer:\n{answer}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session ended by user.")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    
    def interactive_analysis(self, cluster_name: str, log_events: List[Dict], hours_back: int):
        """Interactive Q&A session about the logs"""
        formatted_logs = self.format_logs_for_bedrock(log_events, hours_back)
        
        print("\n" + "="*80)
        print("🤖 INTERACTIVE EKS LOG ANALYSIS")
        print("="*80)
        print("\nYou can now ask questions about your EKS cluster logs!")
        print("\nExample questions:")
        print("  • What API requests do you see?")
        print("  • Show me authentication failures")
        print("  • Which users accessed the cluster?")
        print("  • Are there any errors or warnings?")
        print("  • What pods were created or deleted?")
        print("  • Show me suspicious activities")
        print("\nType 'exit' or 'quit' to end the session.\n")
        
        while True:
            try:
                question = input("\n🔍 Your question: ").strip()
                
                if question.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if not question:
                    continue
                
                print("\n🤔 Analyzing logs...")
                answer = self.ask_bedrock(formatted_logs, question)
                print(f"\n💡 Answer:\n{answer}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session ended by user.")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")


    def show_cluster_info(self):
        """Show information about all EKS clusters"""
        print("\n" + "="*80)
        print("📊 EKS CLUSTER INFORMATION")
        print("="*80)
        
        clusters = self.list_clusters()
        
        print(f"\n🌍 Region: {self.region_name}")
        print(f"📦 Total EKS Clusters: {len(clusters)}")
        
        if not clusters:
            print("\n⚠️  No EKS clusters found in this region.")
            print("\nTo create an EKS cluster:")
            print("  • Use AWS Console: https://console.aws.amazon.com/eks/")
            print("  • Or AWS CLI: aws eks create-cluster --name my-cluster ...")
            return
        
        print(f"\n{'#':<5} {'Cluster Name':<30} {'Status':<15} {'Version':<10}")
        print("-" * 80)
        
        for idx, cluster_name in enumerate(clusters, 1):
            try:
                response = self.eks_client.describe_cluster(name=cluster_name)
                cluster_data = response['cluster']
                
                status = cluster_data.get('status', 'UNKNOWN')
                version = cluster_data.get('version', 'N/A')
                
                # Status emoji
                status_emoji = "✅" if status == "ACTIVE" else "⚠️"
                
                print(f"{idx:<5} {cluster_name:<30} {status_emoji} {status:<13} {version:<10}")
                
            except Exception as e:
                print(f"{idx:<5} {cluster_name:<30} ❌ Error: {str(e)[:20]}")
        
        print("\n" + "="*80)
        print("💡 Tip: Use Mode 1 to analyze logs or Mode 2 to ask questions about these clusters")
        print("="*80)


def main():
    """Main function to run the EKS Log Analyzer"""
    print("\n" + "="*80)
    print("🚀 EKS LOG ANALYZER WITH AWS BEDROCK")
    print("="*80)
    
    try:
        # Initialize analyzer
        analyzer = EKSLogAnalyzer()
        
        # Ask user what they want to do
        print("\n📋 What would you like to do?")
        print("   1. Analyze EKS cluster logs (retrieve and analyze actual logs)")
        print("   2. Ask general EKS questions (knowledge assistant)")
        print("   3. Show my cluster information (quick view)")
        
        mode = input("\nEnter your choice (1, 2, or 3): ").strip()
        
        if mode == "3":
            # Show cluster information
            analyzer.show_cluster_info()
            return
        
        if mode == "2":
            # General EKS knowledge mode
            print("\n🤖 Starting EKS Knowledge Assistant...")
            
            # Optionally get cluster context
            print("\n📋 Available EKS clusters:")
            clusters = analyzer.list_clusters()
            if clusters:
                for idx, cluster in enumerate(clusters, 1):
                    print(f"   {idx}. {cluster}")
                
                cluster_input = input("\n🎯 Enter cluster name for context (or press Enter to skip): ").strip()
                cluster_name = cluster_input if cluster_input else None
            else:
                print("   No clusters found (but you can still ask general questions)")
                cluster_name = None
            
            analyzer.interactive_general_mode(cluster_name)
            return
        
        # Mode 1: Log analysis
        # List available clusters
        print("\n📋 Available EKS clusters:")
        clusters = analyzer.list_clusters()
        if clusters:
            for idx, cluster in enumerate(clusters, 1):
                print(f"   {idx}. {cluster}")
        else:
            print("   No clusters found in this region")
            return
        
        # Get cluster name from user
        cluster_input = input("\n🎯 Enter your EKS cluster name (or number): ").strip()
        
        if not cluster_input:
            print("❌ Cluster name is required!")
            return
        
        # Check if user entered a number
        if cluster_input.isdigit():
            idx = int(cluster_input) - 1
            if 0 <= idx < len(clusters):
                cluster_name = clusters[idx]
                print(f"✅ Selected: {cluster_name}")
            else:
                print(f"❌ Invalid number. Please choose between 1 and {len(clusters)}")
                return
        else:
            cluster_name = cluster_input
        
        # Check if cluster exists
        if not analyzer.check_cluster_exists(cluster_name):
            return
        
        # Check if logging is enabled
        logging_enabled, log_types = analyzer.check_cluster_logging(cluster_name)
        
        if not logging_enabled:
            return
        
        # Get time range
        print("\n⏰ How many hours of logs do you want to analyze?")
        hours_input = input("   Hours (default: 24): ").strip()
        hours_back = int(hours_input) if hours_input else 24
        
        # Retrieve logs
        print(f"\n📥 Retrieving logs for the last {hours_back} hours...")
        log_events = analyzer.retrieve_logs(cluster_name, hours_back, log_types)
        
        if not log_events:
            print("\n⚠️  No logs found. This could mean:")
            print("   • Logging was recently enabled (wait 5-10 minutes)")
            print("   • No activity in the specified time range")
            print("   • Logs are being sent to S3 instead of CloudWatch")
            return
        
        # Start interactive analysis
        analyzer.interactive_analysis(cluster_name, log_events, hours_back)
        
    except KeyboardInterrupt:
        print("\n\n👋 Analyzer stopped by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
