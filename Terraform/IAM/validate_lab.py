import boto3
from datetime import datetime, timedelta

# Configuration
REGION = 'us-east-1'
TARGET_USER = 'ec2-launch-user'

def check_activity():
    print(f"Checking activity for user: {TARGET_USER} in {REGION}...\n")
    
    # 1. CloudTrail Client
    ct_client = boto3.client('cloudtrail', region_name=REGION)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=2)
    
    try:
        response = ct_client.lookup_events(
            LookupAttributes=[
                {'AttributeKey': 'Username', 'AttributeValue': TARGET_USER},
                {'AttributeKey': 'EventName', 'AttributeValue': 'RunInstances'}
            ],
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=1
        )
        
        if response['Events']:
            print("[PASS] User ne EC2 Instance launch ki request bheji thi.")
            event_details = response['Events'][0]
            print(f"   Time: {event_details['EventTime']}")
            print(f"   Event ID: {event_details['EventId']}")
        else:
            print("[FAIL] User ne abhi tak koi EC2 Instance launch nahi kiya.")
            
    except Exception as e:
        print(f"Error checking CloudTrail: {e}")
        print("Note: CloudTrail events reflect hone me kabhi-kabhi 15 mins lagte hain.")

    # 2. EC2 Client (Current Status dekhne ke liye)
    ec2_client = boto3.client('ec2', region_name=REGION)
    
    print("\nChecking current Running Instances...")
    instances = ec2_client.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    
    found_running = False
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            key_name = instance.get('KeyName', 'NoKey')
            print(f"   Found Instance: {instance['InstanceId']} | Key: {key_name}")
            found_running = True

    if found_running:
        print("[PASS] Active Running Instance found.")
    else:
        print("[WARNING] Instance launch hua tha par abhi running nahi hai (shayad terminate kar diya).")

if __name__ == "__main__":
    check_activity()

