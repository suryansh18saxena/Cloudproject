"""
Boto3 validation functions for lab scoring.
Each function checks a specific AWS task and returns a dict:
  {"task_name": str, "passed": bool, "details": str}
"""

import boto3
from datetime import datetime, timedelta


REGION = 'us-east-1'


def _get_clients():
    """Create boto3 clients."""
    return {
        'ct': boto3.client('cloudtrail', region_name=REGION),
        'ec2': boto3.client('ec2', region_name=REGION),
    }


def check_ec2_launched(iam_username):
    """Check if the user launched an EC2 instance via CloudTrail."""
    try:
        ct = boto3.client('cloudtrail', region_name=REGION)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=2)

        response = ct.lookup_events(
            LookupAttributes=[
                {'AttributeKey': 'Username', 'AttributeValue': iam_username},
            ],
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=50,
        )

        # Filter for RunInstances events
        run_events = [
            e for e in response.get('Events', [])
            if e.get('EventName') == 'RunInstances'
        ]

        if run_events:
            event = run_events[0]
            return {
                'task_name': 'EC2 Instance Launch',
                'passed': True,
                'details': f"Instance launch detected at {event['EventTime']}. Event ID: {event['EventId']}",
            }
        else:
            return {
                'task_name': 'EC2 Instance Launch',
                'passed': False,
                'details': 'No RunInstances event found in CloudTrail. Note: Events may take up to 15 minutes to appear.',
            }
    except Exception as e:
        return {
            'task_name': 'EC2 Instance Launch',
            'passed': False,
            'details': f'Error checking CloudTrail: {str(e)}',
        }


def check_ec2_running(iam_username):
    """Check if there is a running EC2 instance."""
    try:
        ec2 = boto3.client('ec2', region_name=REGION)

        response = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']},
            ]
        )

        running_instances = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                running_instances.append({
                    'id': instance['InstanceId'],
                    'type': instance.get('InstanceType', 'unknown'),
                    'key': instance.get('KeyName', 'NoKey'),
                    'launch_time': str(instance.get('LaunchTime', '')),
                })

        if running_instances:
            instance_info = running_instances[0]
            return {
                'task_name': 'EC2 Instance Running',
                'passed': True,
                'details': f"Running instance found: {instance_info['id']} (Type: {instance_info['type']}, Key: {instance_info['key']})",
            }
        else:
            return {
                'task_name': 'EC2 Instance Running',
                'passed': False,
                'details': 'No running EC2 instances found. The instance may have been stopped or terminated.',
            }
    except Exception as e:
        return {
            'task_name': 'EC2 Instance Running',
            'passed': False,
            'details': f'Error checking EC2: {str(e)}',
        }


def check_security_group(iam_username):
    """Check if a security group with SSH (port 22) access exists."""
    try:
        ec2 = boto3.client('ec2', region_name=REGION)

        # Get all non-default security groups
        response = ec2.describe_security_groups()

        ssh_sg_found = False
        sg_details = ''

        for sg in response.get('SecurityGroups', []):
            # Skip the default security group
            if sg['GroupName'] == 'default':
                continue

            for perm in sg.get('IpPermissions', []):
                from_port = perm.get('FromPort', 0)
                to_port = perm.get('ToPort', 0)
                if from_port <= 22 <= to_port:
                    ssh_sg_found = True
                    sg_details = f"Security Group '{sg['GroupName']}' (ID: {sg['GroupId']}) has SSH access on port 22."
                    break
            if ssh_sg_found:
                break

        if ssh_sg_found:
            return {
                'task_name': 'Security Group (SSH)',
                'passed': True,
                'details': sg_details,
            }
        else:
            return {
                'task_name': 'Security Group (SSH)',
                'passed': False,
                'details': 'No security group found with SSH (port 22) inbound rule.',
            }
    except Exception as e:
        return {
            'task_name': 'Security Group (SSH)',
            'passed': False,
            'details': f'Error checking Security Groups: {str(e)}',
        }


def validate_all_tasks(iam_username):
    """
    Run all validation checks and return a list of results.
    Returns: list of {"task_name": str, "passed": bool, "details": str}
    """
    # 1. Pehle saare individual checks run karein
    launched_result = check_ec2_launched(iam_username)
    running_result = check_ec2_running(iam_username)
    sg_result = check_security_group(iam_username)

    # 2. SMART BYPASS FOR CLOUDTRAIL DELAY
    # Agar instance running hai, par CloudTrail log abhi tak nahi aaya, 
    # toh hum Launch wale task ko automatically Pass kar denge.
    if running_result['passed'] and not launched_result['passed']:
        launched_result['passed'] = True
        launched_result['details'] = "Running instance detected. Bypassing AWS CloudTrail delay to verify launch."

    # 3. Final results return karein
    results = [
        launched_result,
        running_result,
        sg_result,
    ]
    
    return results


def calculate_score(validation_results):
    """
    Calculate score from validation results.
    Returns: {"total_tasks": int, "passed_tasks": int, "score_percentage": float}
    """
    total = len(validation_results)
    passed = sum(1 for r in validation_results if r['passed'])
    percentage = (passed / total * 100) if total > 0 else 0

    return {
        'total_tasks': total,
        'passed_tasks': passed,
        'score_percentage': round(percentage, 1),
    }
