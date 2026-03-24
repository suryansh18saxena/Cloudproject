import boto3
import sys
import time

# Region wahi rakhein jo aap use kar rahe hain
REGION = 'us-east-1'

def cleanup_resources(username):
    print(f"[INFO] Starting cleanup for user: {username}...")
    
    # Clients initialize
    ct_client = boto3.client('cloudtrail', region_name=REGION)
    ec2_client = boto3.client('ec2', region_name=REGION)

    # 1. CloudTrail se Resource IDs dhundhein
    print("[SEARCH] Scanning CloudTrail for created instances...")
    
    try:
        response = ct_client.lookup_events(
            LookupAttributes=[
                {'AttributeKey': 'Username', 'AttributeValue': username},
                {'AttributeKey': 'EventName', 'AttributeValue': 'RunInstances'}
            ],
            MaxResults=50
        )
        
        instance_ids = []
        
        for event in response.get('Events', []):
            for resource in event.get('Resources', []):
                if resource['ResourceType'] == 'AWS::EC2::Instance':
                    instance_ids.append(resource['ResourceName'])

        # Duplicates hatayein
        instance_ids = list(set(instance_ids))

        if not instance_ids:
            print("[OK] No instances found in CloudTrail history for this user.")
            return

        print(f"[WARN] Found instances launched by user: {instance_ids}")

        # 2. Check karein ki kya ye instances abhi bhi Running hain?
        running_instances = ec2_client.describe_instances(
            InstanceIds=instance_ids,
            Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}]
        )
        
        ids_to_terminate = []
        for r in running_instances['Reservations']:
            for i in r['Instances']:
                ids_to_terminate.append(i['InstanceId'])

        if ids_to_terminate:
            print(f"[DELETE] Terminating instances: {ids_to_terminate}...")
            ec2_client.terminate_instances(InstanceIds=ids_to_terminate)
            
            # Wait for termination
            print("[WAIT] Waiting for instances to shut down...")
            waiter = ec2_client.get_waiter('instance_terminated')
            waiter.wait(InstanceIds=ids_to_terminate)
            print("[OK] Instances destroyed successfully.")
        else:
            print("[OK] Instances already terminated.")

    except Exception as e:
        print(f"[ERROR] Error during cleanup: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup_user.py <iam_username>")
        sys.exit(1)
    
    cleanup_resources(sys.argv[1])