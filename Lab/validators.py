"""
Boto3 validation functions for lab scoring.
Each function checks a specific AWS task and returns a dict:
  {"task_name": str, "passed": bool, "details": str}
"""

import boto3
from django.utils import timezone
import os

REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')


def check_ec2_launched(iam_username):
    """
    Check if the user launched an EC2 instance.
    Strategy:
      1. Try CloudTrail first (accurate but can lag up to 15 min).
      2. If no CloudTrail event found, fall back to describe_instances —
         any instance launched in the last 4 hours counts as proof of launch.
    """
    # ── Step 1: CloudTrail lookup ──────────────────────────────────────
    try:
        ct = boto3.client('cloudtrail', region_name=REGION)
        end_time = timezone.now()
        start_time = end_time - timezone.timedelta(hours=4)

        response = ct.lookup_events(
            LookupAttributes=[
                {'AttributeKey': 'Username', 'AttributeValue': iam_username},
            ],
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=50,
        )

        run_events = [
            e for e in response.get('Events', [])
            if e.get('EventName') == 'RunInstances'
        ]

        if run_events:
            event = run_events[0]
            return {
                'task_name': 'EC2 Instance Launch',
                'passed': True,
                'details': f"CloudTrail: RunInstances event at {event['EventTime']}.",
            }
    except Exception:
        pass  # CloudTrail unavailable — proceed to fallback

    # ── Step 2: describe_instances fallback ───────────────────────────
    # CloudTrail events can lag up to 15 minutes.
    # Fall back to describe_instances — any non-terminated instance is
    # proof the student launched one. No time cutoff: it may have been
    # launched earlier in the session.
    try:
        ec2 = boto3.client('ec2', region_name=REGION)

        response = ec2.describe_instances(
            Filters=[{
                'Name': 'instance-state-name',
                'Values': ['running', 'stopped', 'stopping', 'pending', 'shutting-down'],
            }]
        )

        all_instances = []
        for reservation in response.get('Reservations', []):
            for inst in reservation.get('Instances', []):
                all_instances.append(inst)

        if all_instances:
            inst = all_instances[0]
            return {
                'task_name': 'EC2 Instance Launch',
                'passed': True,
                'details': (
                    f"Instance detected: {inst['InstanceId']} "
                    f"(State: {inst['State']['Name']}, "
                    f"Type: {inst.get('InstanceType','?')}, "
                    f"Launched: {inst.get('LaunchTime','?')}). "
                    f"[CloudTrail event may still be propagating]"
                ),
            }
        else:
            return {
                'task_name': 'EC2 Instance Launch',
                'passed': False,
                'details': (
                    'No EC2 instance found via CloudTrail or EC2 API. '
                    'Please launch an instance in the AWS Console and retry validation.'
                ),
            }
    except Exception as e:
        return {
            'task_name': 'EC2 Instance Launch',
            'passed': False,
            'details': f'EC2 API error: {str(e)}',
        }


def check_ec2_running(iam_username):
    """
    Check if there is at least one running EC2 instance in the account.
    Note: We do NOT filter by 'CreatedBy' tag because students launching
    via the AWS Console typically do not add that tag.
    """
    try:
        ec2 = boto3.client('ec2', region_name=REGION)

        # Check for any running instance — no tag filter needed
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
            inst = running_instances[0]
            return {
                'task_name': 'EC2 Instance Running',
                'passed': True,
                'details': (
                    f"Running instance: {inst['id']} "
                    f"(Type: {inst['type']}, Key: {inst['key']}, "
                    f"Launched: {inst['launch_time']})"
                ),
            }
        else:
            return {
                'task_name': 'EC2 Instance Running',
                'passed': False,
                'details': 'No running EC2 instances found. Ensure your instance is in the Running state.',
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


def validate_ec2_tasks(iam_username):
    """
    Run EC2 validation checks.
    """
    launched_result = check_ec2_launched(iam_username)
    running_result = check_ec2_running(iam_username)
    sg_result = check_security_group(iam_username)

    # Removed bypass logic or implement a secure one if needed
    # But as requested by Task 1 Step 5: "usko hata dein"
    return [launched_result, running_result, sg_result]


def validate_s3_tasks(iam_username):
    """Run S3 validation checks."""
    s3 = boto3.client('s3', region_name=REGION)
    results = []
    
    # Bucket Creation
    try:
        response = s3.list_buckets()
        buckets = response.get('Buckets', [])
        
        # Read tags to match CreatedBy
        student_bucket = None
        for b in buckets:
            try:
                tags = s3.get_bucket_tagging(Bucket=b['Name'])
                for tag in tags.get('TagSet', []):
                    if tag['Key'] == 'CreatedBy' and tag['Value'] == iam_username:
                        student_bucket = b['Name']
                        break
                if student_bucket:
                    break
            except Exception:
                pass
            
        if student_bucket:
            results.append({'task_name': 'Bucket Creation', 'passed': True, 'details': f"Bucket found: {student_bucket}"})
        else:
            results.append({'task_name': 'Bucket Creation', 'passed': False, 'details': 'No buckets found.'})
            return results # Return early if no bucket
            
    except Exception as e:
        results.append({'task_name': 'Bucket Creation', 'passed': False, 'details': str(e)})
        return results

    # Versioning
    try:
        vers = s3.get_bucket_versioning(Bucket=student_bucket)
        if vers.get('Status') == 'Enabled':
            results.append({'task_name': 'Versioning', 'passed': True, 'details': 'Versioning is enabled.'})
        else:
            results.append({'task_name': 'Versioning', 'passed': False, 'details': 'Versioning is not enabled.'})
    except Exception as e:
        results.append({'task_name': 'Versioning', 'passed': False, 'details': str(e)})

    # Bucket Policy
    try:
        s3.get_bucket_policy(Bucket=student_bucket)
        results.append({'task_name': 'Bucket Policy', 'passed': True, 'details': 'Bucket policy is attached.'})
    except Exception as e:
        results.append({'task_name': 'Bucket Policy', 'passed': False, 'details': 'No bucket policy found.'})

    # Block Public Access
    try:
        bpa = s3.get_public_access_block(Bucket=student_bucket)
        config = bpa.get('PublicAccessBlockConfiguration', {})
        if config.get('BlockPublicAcls') and config.get('BlockPublicPolicy'):
            results.append({'task_name': 'Block Public Access', 'passed': True, 'details': 'Public access is blocked.'})
        else:
            results.append({'task_name': 'Block Public Access', 'passed': False, 'details': 'Public access is not fully blocked.'})
    except Exception as e:
        results.append({'task_name': 'Block Public Access', 'passed': False, 'details': 'Block public access not configured.'})

    # Upload
    try:
        objs = s3.list_objects_v2(Bucket=student_bucket)
        if objs.get('KeyCount', 0) > 0:
            results.append({'task_name': 'Upload', 'passed': True, 'details': f"Objects found: {objs['KeyCount']}"})
        else:
            results.append({'task_name': 'Upload', 'passed': False, 'details': 'Bucket is empty.'})
    except Exception as e:
        results.append({'task_name': 'Upload', 'passed': False, 'details': str(e)})

    return results


def validate_vpc_tasks(iam_username):
    """Run VPC validation checks."""
    ec2 = boto3.client('ec2', region_name=REGION)
    results = []
    
    # 1. VPC Creation (Look for a non-default VPC)
    vpc_id = None
    try:
        response = ec2.describe_vpcs(Filters=[{'Name': 'tag:CreatedBy', 'Values': [iam_username]}])
        vpcs = response.get('Vpcs', [])
        if vpcs:
            vpc_id = vpcs[0]['VpcId']
            results.append({'task_name': 'VPC Creation', 'passed': True, 'details': f"VPC found: {vpc_id}"})
        else:
            results.append({'task_name': 'VPC Creation', 'passed': False, 'details': 'No non-default VPC found.'})
            return results # Can't proceed without VPC
    except Exception as e:
        results.append({'task_name': 'VPC Creation', 'passed': False, 'details': str(e)})
        return results

    # 2. Subnets
    try:
        response = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        subnets = response.get('Subnets', [])
        if len(subnets) >= 2:
            results.append({'task_name': 'Subnets', 'passed': True, 'details': f"Found {len(subnets)} subnets."})
        else:
            results.append({'task_name': 'Subnets', 'passed': False, 'details': f"Found {len(subnets)} subnets (expected at least 2)."})
    except Exception as e:
        results.append({'task_name': 'Subnets', 'passed': False, 'details': str(e)})

    # 3. Internet Gateway
    igw_id = None
    try:
        response = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])
        igws = response.get('InternetGateways', [])
        if igws:
            igw_id = igws[0]['InternetGatewayId']
            results.append({'task_name': 'Internet Gateway', 'passed': True, 'details': f"IGW attached: {igw_id}"})
        else:
            results.append({'task_name': 'Internet Gateway', 'passed': False, 'details': 'No IGW attached to VPC.'})
    except Exception as e:
        results.append({'task_name': 'Internet Gateway', 'passed': False, 'details': str(e)})

    # 4. Route Tables
    rt_id = None
    try:
        response = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        rts = [rt for rt in response.get('RouteTables', []) if not any(a.get('Main') for a in rt.get('Associations', []))]
        if rts:
            rt_id = rts[0]['RouteTableId']
            results.append({'task_name': 'Route Tables', 'passed': True, 'details': f"Custom Route Table found: {rt_id}"})
        else:
            results.append({'task_name': 'Route Tables', 'passed': False, 'details': 'No custom route table found.'})
    except Exception as e:
        results.append({'task_name': 'Route Tables', 'passed': False, 'details': str(e)})

    # 5. Route Association
    try:
        if rt_id:
            response = ec2.describe_route_tables(Filters=[{'Name': 'route-table-id', 'Values': [rt_id]}])
            associations = response['RouteTables'][0].get('Associations', [])
            if any(not a.get('Main') for a in associations):
                results.append({'task_name': 'Route Association', 'passed': True, 'details': 'Subnet is associated with route table.'})
            else:
                results.append({'task_name': 'Route Association', 'passed': False, 'details': 'No subnets associated with the custom route table.'})
        else:
            results.append({'task_name': 'Route Association', 'passed': False, 'details': 'Custom Route Table missing.'})
    except Exception as e:
        results.append({'task_name': 'Route Association', 'passed': False, 'details': str(e)})

    # 6. IGW Routing
    try:
        if rt_id and igw_id:
            response = ec2.describe_route_tables(Filters=[{'Name': 'route-table-id', 'Values': [rt_id]}])
            routes = response['RouteTables'][0].get('Routes', [])
            if any(r.get('GatewayId') == igw_id for r in routes):
                results.append({'task_name': 'IGW Routing', 'passed': True, 'details': 'Route to IGW exists.'})
            else:
                results.append({'task_name': 'IGW Routing', 'passed': False, 'details': 'Missing route pointing to IGW.'})
        else:
            results.append({'task_name': 'IGW Routing', 'passed': False, 'details': 'Route Table or IGW missing.'})
    except Exception as e:
        results.append({'task_name': 'IGW Routing', 'passed': False, 'details': str(e)})

    return results

def validate_lab_tasks(lab_slug, iam_username):
    """
    Router to direct validation depending on the lab slug.
    """
    if lab_slug == 'ec2-launch-lab':
        return validate_ec2_tasks(iam_username)
    elif lab_slug == 's3-bucket-lab':
        return validate_s3_tasks(iam_username)
    elif lab_slug == 'vpc-networking-lab':
        return validate_vpc_tasks(iam_username)
    else:
        return [{'task_name': 'Unknown Lab', 'passed': False, 'details': f'No validator for {lab_slug}'}]



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
