import boto3
from datetime import datetime, timedelta

# Configuration
# Wahi region dalein jo aapne terraform variables.tf mein use kiya tha
REGION = 'us-east-1'
TARGET_USER = 'ec2-launch-user'

def check_activity():
    print(f"Checking activity for user: {TARGET_USER} in {REGION}...\n")
    
    # 1. CloudTrail Client (History track karne ke liye)
    ct_client = boto3.client('cloudtrail', region_name=REGION)
    
    # Pichle 2 ghante ke events dhundho
    start_time = datetime.now() - timedelta(hours=2)
    
    try:
        # CloudTrail se pucho: Kya is user ne 'RunInstances' call kiya?
        response = ct_client.lookup_events(
            LookupAttributes=[
                {'AttributeKey': 'Username', 'AttributeValue': TARGET_USER},
                {'AttributeKey': 'EventName', 'AttributeValue': 'RunInstances'}
            ],
            StartTime=start_time,
            MaxResults=1
        )
        
        if response['Events']:
            print("✅ [PASS] User ne EC2 Instance launch ki request bheji thi.")
            event_details = response['Events'][0]
            print(f"   Time: {event_details['EventTime']}")
            print(f"   Event ID: {event_details['EventId']}")
        else:
            print("❌ [FAIL] User ne abhi tak koi EC2 Instance launch nahi kiya.")
            return # Aage check karne ka fayda nahi
            
    except Exception as e:
        print(f"Error checking CloudTrail: {e}")
        print("Note: CloudTrail events reflect hone me kabhi-kabhi 15 mins lagte hain.")

    # 2. EC2 Client (Current Status dekhne ke liye)
    ec2_client = boto3.client('ec2', region_name=REGION)
    
    # Check karo ki kya koi instance abhi 'running' state mein hai?
    # (Note: Hum tag se filter nahi kar rahe kyunki user shayad tag lagana bhool gaya ho, 
    # hum bas dekhenge ki kya koi instance running hai jo is key-pair se bana ho)
    
    print("\nChecking current Running Instances...")
    instances = ec2_client.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    
    found_running = False
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            # Hum check kar sakte hain ki kya key-name match kar raha hai (optional validation)
            key_name = instance.get('KeyName', 'NoKey')
            print(f"   Found Instance: {instance['InstanceId']} | Key: {key_name}")
            found_running = True

    if found_running:
        print("✅ [PASS] Active Running Instance found.")
    else:
        print("⚠️ [WARNING] Instance launch hua tha par abhi running nahi hai (shayad terminate kar diya).")

if __name__ == "__main__":
    # Ensure karein ki aapke paas ADMIN credentials set hain taaki aap check kar sakein
    check_activity()