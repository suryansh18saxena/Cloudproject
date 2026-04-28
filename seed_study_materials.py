"""
Seed script to populate Study Materials for all existing labs.
Run: python manage.py shell < seed_study_materials.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Cloud_Project.settings')
django.setup()

from Lab.models import Lab, StudyMaterial, StudySection

# ─── EC2 STUDY MATERIAL ────────────────────────────────────────
ec2_lab = Lab.objects.filter(slug='ec2-launch-lab').first()
if ec2_lab:
    mat, created = StudyMaterial.objects.update_or_create(
        lab=ec2_lab,
        defaults={
            'title': 'Amazon EC2 - Complete Guide to Elastic Compute Cloud',
            'overview': 'Amazon EC2 (Elastic Compute Cloud) is one of the most fundamental AWS services. It provides resizable compute capacity in the cloud, allowing you to launch virtual servers (instances) on demand. This guide covers everything from EC2 basics to launching, configuring security groups, attaching IAM roles, and best practices for production workloads.',
            'icon': 'dns',
            'estimated_read_minutes': 20,
            'prerequisites': 'Basic understanding of cloud computing concepts\nAWS account access (provided in the lab)\nFamiliarity with the AWS Management Console\nBasic knowledge of networking (IP addresses, ports)',
            'learning_outcomes': 'Understand what EC2 instances are and how they work\nLearn to choose the right instance type for your workload\nConfigure Security Groups for network access control\nAttach IAM roles to EC2 instances for secure API access\nLaunch and manage EC2 instances via the AWS Console',
        }
    )
    sections_data = [
        {
            'order': 1,
            'title': 'What is Amazon EC2?',
            'section_type': 'theory',
            'icon': 'cloud',
            'content': '<p>Amazon Elastic Compute Cloud (EC2) is a web service that provides <strong>resizable compute capacity</strong> in the cloud. Think of it as renting virtual computers on which you can run your own applications.</p><p>EC2 eliminates the need to invest in hardware upfront, so you can develop and deploy applications faster. You can launch as many or as few virtual servers as you need, configure security and networking, and manage storage.</p><p><strong>Key concepts:</strong></p><p>• <strong>Instance</strong> — A virtual server in the cloud<br>• <strong>AMI (Amazon Machine Image)</strong> — A template containing the OS and software configuration<br>• <strong>Instance Type</strong> — Defines the hardware (CPU, memory, storage, network)<br>• <strong>EBS (Elastic Block Store)</strong> — Persistent block storage volumes for instances<br>• <strong>Key Pair</strong> — Used for SSH authentication to connect to instances</p>',
            'code_example': '# List running instances using AWS CLI\naws ec2 describe-instances \\\n  --filters "Name=instance-state-name,Values=running" \\\n  --query "Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,State:State.Name}" \\\n  --output table',
            'code_language': 'bash',
            'tip': 'EC2 instances are billed per second (minimum 60 seconds). Always stop or terminate instances you are not using to avoid unnecessary charges.',
            'key_takeaway': 'EC2 provides virtual servers (instances) in the cloud that you can launch, configure, and scale on demand without upfront hardware investment.',
        },
        {
            'order': 2,
            'title': 'EC2 Instance Types Explained',
            'section_type': 'concept',
            'icon': 'memory',
            'content': '<p>Instance types determine the <strong>hardware of the host computer</strong> used for your instance. Each instance type offers a different balance of compute, memory, storage, and networking capacity.</p><p><strong>Instance families:</strong></p><p>• <strong>General Purpose (t2, t3, m5)</strong> — Balanced compute, memory, and networking. Ideal for web servers and small databases. <code>t2.micro</code> is free-tier eligible.<br>• <strong>Compute Optimized (c5, c6g)</strong> — High-performance processors for batch processing, gaming servers, machine learning inference.<br>• <strong>Memory Optimized (r5, x1)</strong> — For memory-intensive workloads like in-memory databases (Redis, Memcached).<br>• <strong>Storage Optimized (i3, d2)</strong> — High sequential read/write access to large datasets on local storage.<br>• <strong>Accelerated Computing (p3, g4)</strong> — GPU instances for machine learning training, video rendering.</p><p>For this lab, we use <strong>t2.micro</strong> — it provides 1 vCPU, 1 GiB RAM, and is part of the AWS Free Tier.</p>',
            'code_example': '# Check available instance types in a region\naws ec2 describe-instance-types \\\n  --filters "Name=instance-type,Values=t2.*" \\\n  --query "InstanceTypes[].{Type:InstanceType,vCPUs:VCpuInfo.DefaultVCpus,Memory:MemoryInfo.SizeInMiB}" \\\n  --output table',
            'code_language': 'bash',
            'tip': 'Use t3.micro instead of t2.micro for newer workloads — t3 instances use the Nitro hypervisor and offer better performance at the same price.',
            'key_takeaway': 'Choose your instance type based on your workload requirements. For learning and development, t2.micro (free tier) is the ideal starting point.',
        },
        {
            'order': 3,
            'title': 'Security Groups - Virtual Firewalls',
            'section_type': 'concept',
            'icon': 'shield',
            'content': '<p>A <strong>Security Group</strong> acts as a virtual firewall for your EC2 instances to control <strong>inbound and outbound traffic</strong>. When you launch an instance, you associate one or more security groups with it.</p><p><strong>Key rules:</strong></p><p>• Security groups are <strong>stateful</strong> — if you send a request from your instance, the response traffic is automatically allowed, regardless of inbound rules.<br>• By default, all <strong>inbound traffic is denied</strong> and all <strong>outbound traffic is allowed</strong>.<br>• You can only create <strong>allow rules</strong>, not deny rules.<br>• Changes take effect <strong>immediately</strong>.</p><p><strong>Common inbound rules:</strong></p><p>• <strong>SSH (port 22)</strong> — For remote terminal access to Linux instances<br>• <strong>HTTP (port 80)</strong> — For web server traffic<br>• <strong>HTTPS (port 443)</strong> — For secure web traffic<br>• <strong>RDP (port 3389)</strong> — For Windows Remote Desktop access</p>',
            'code_example': '# Create a security group\naws ec2 create-security-group \\\n  --group-name my-ssh-sg \\\n  --description "Allow SSH from my IP"\n\n# Add SSH inbound rule\naws ec2 authorize-security-group-ingress \\\n  --group-name my-ssh-sg \\\n  --protocol tcp \\\n  --port 22 \\\n  --cidr 203.0.113.0/32',
            'code_language': 'bash',
            'tip': 'Never use 0.0.0.0/0 (open to the world) for SSH access in production. Always restrict to specific IP addresses or use AWS Systems Manager Session Manager for secure access.',
            'key_takeaway': 'Security Groups are stateful firewalls that control traffic to your instances. Always follow the principle of least privilege — only open ports that are necessary.',
        },
        {
            'order': 4,
            'title': 'IAM Roles for EC2',
            'section_type': 'best_practice',
            'icon': 'admin_panel_settings',
            'content': '<p>An <strong>IAM Role</strong> is an identity with specific permissions that can be assumed by AWS services. When attached to an EC2 instance, the instance can securely access other AWS services <strong>without hardcoding credentials</strong>.</p><p><strong>How it works:</strong></p><p>1. Create an IAM Role with a trust policy allowing EC2 to assume it<br>2. Attach permission policies (e.g., S3ReadOnly, DynamoDBFullAccess)<br>3. Create an Instance Profile (a container for the role)<br>4. Attach the Instance Profile to your EC2 instance</p><p><strong>Why use IAM Roles instead of access keys?</strong></p><p>• <strong>No credentials to manage</strong> — AWS handles temporary credentials automatically<br>• <strong>Automatic rotation</strong> — Temporary credentials are rotated every few hours<br>• <strong>Secure</strong> — No risk of accidentally leaking access keys in code or logs</p>',
            'code_example': '# Create an IAM role for EC2\naws iam create-role \\\n  --role-name EC2-S3-ReadOnly \\\n  --assume-role-policy-document file://trust-policy.json\n\n# Attach a policy to the role\naws iam attach-role-policy \\\n  --role-name EC2-S3-ReadOnly \\\n  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess',
            'code_language': 'bash',
            'tip': 'Always use IAM Roles for EC2 instances instead of storing AWS access keys on the instance. This is an AWS security best practice and is often tested in certification exams.',
            'key_takeaway': 'IAM Roles provide temporary, automatically-rotated credentials to EC2 instances, eliminating the need for hardcoded access keys.',
        },
        {
            'order': 5,
            'title': 'Launching Your First EC2 Instance',
            'section_type': 'hands_on',
            'icon': 'rocket_launch',
            'content': '<p>Here is a <strong>step-by-step walkthrough</strong> of launching an EC2 instance via the AWS Console:</p><p><strong>Step 1:</strong> Navigate to the EC2 Dashboard → Click "Launch instances"<br><strong>Step 2:</strong> Enter a name for your instance (e.g., "my-web-server")<br><strong>Step 3:</strong> Select an AMI — choose <strong>Amazon Linux 2</strong> (free tier eligible)<br><strong>Step 4:</strong> Choose instance type — select <strong>t2.micro</strong><br><strong>Step 5:</strong> Configure Key Pair — select an existing key pair or create a new one<br><strong>Step 6:</strong> Network Settings — create a new security group with SSH access<br><strong>Step 7:</strong> Storage — keep the default 8 GiB gp2 volume<br><strong>Step 8:</strong> Advanced Details — select the IAM instance profile<br><strong>Step 9:</strong> Click "Launch instance" and wait for it to start</p><p>Once launched, your instance will go through the states: <strong>pending → running</strong>. You can then connect via SSH using your key pair.</p>',
            'code_example': '# Connect to your instance via SSH\nssh -i "my-key-pair.pem" ec2-user@<public-ip-address>\n\n# Verify the instance metadata\ncurl http://169.254.169.254/latest/meta-data/instance-id\ncurl http://169.254.169.254/latest/meta-data/instance-type',
            'code_language': 'bash',
            'tip': 'Always check that your instance state shows "running" and the status checks show "2/2 checks passed" before attempting to connect.',
            'key_takeaway': 'Launching an EC2 instance involves selecting an AMI, instance type, key pair, security group, and optionally an IAM role. The entire process takes under 2 minutes.',
        },
    ]
    StudySection.objects.filter(material=mat).delete()
    for s in sections_data:
        StudySection.objects.create(material=mat, **s)
    print(f"✅ EC2 study material seeded: {mat.title}")

# ─── S3 STUDY MATERIAL ────────────────────────────────────────
s3_lab = Lab.objects.filter(slug='s3-bucket-lab').first()
if s3_lab:
    mat, created = StudyMaterial.objects.update_or_create(
        lab=s3_lab,
        defaults={
            'title': 'Amazon S3 - Complete Guide to Simple Storage Service',
            'overview': 'Amazon S3 (Simple Storage Service) is an object storage service offering industry-leading scalability, data availability, security, and performance. This guide covers S3 buckets, objects, permissions, versioning, lifecycle policies, and best practices for secure and cost-effective storage.',
            'icon': 'cloud_upload',
            'estimated_read_minutes': 18,
            'prerequisites': 'Basic understanding of cloud storage concepts\nAWS account access (provided in the lab)\nFamiliarity with file systems and permissions',
            'learning_outcomes': 'Understand S3 buckets, objects, and storage classes\nConfigure bucket policies and ACLs for access control\nEnable versioning and lifecycle rules\nUpload and manage objects via Console and CLI\nApply S3 security best practices',
        }
    )
    sections_data = [
        {
            'order': 1,
            'title': 'What is Amazon S3?',
            'section_type': 'theory',
            'icon': 'storage',
            'content': '<p>Amazon S3 is an <strong>object storage service</strong> that stores data as objects within buckets. An object consists of the data file, metadata, and a unique key (name).</p><p><strong>Key concepts:</strong></p><p>• <strong>Bucket</strong> — A container for objects. Bucket names must be globally unique.<br>• <strong>Object</strong> — A file and its metadata, identified by a key.<br>• <strong>Key</strong> — The unique name for an object within a bucket.<br>• <strong>Region</strong> — You choose the region where S3 stores your bucket data.<br>• <strong>Storage Class</strong> — Controls cost vs. availability (Standard, IA, Glacier, etc.)</p><p>S3 provides <strong>99.999999999% (11 nines) durability</strong> and <strong>99.99% availability</strong>.</p>',
            'code_example': '# Create an S3 bucket\naws s3 mb s3://my-unique-bucket-name-2024 --region us-east-1\n\n# List all buckets\naws s3 ls\n\n# Upload a file\naws s3 cp myfile.txt s3://my-unique-bucket-name-2024/',
            'code_language': 'bash',
            'tip': 'S3 bucket names are globally unique across all AWS accounts. Use a naming convention like "company-project-environment" to avoid conflicts.',
            'key_takeaway': 'S3 provides virtually unlimited, highly durable object storage. Data is organized in buckets and accessed via unique keys.',
        },
        {
            'order': 2,
            'title': 'S3 Storage Classes',
            'section_type': 'concept',
            'icon': 'layers',
            'content': '<p>S3 offers multiple <strong>storage classes</strong> designed for different use cases and cost profiles:</p><p>• <strong>S3 Standard</strong> — High durability, availability. For frequently accessed data.<br>• <strong>S3 Intelligent-Tiering</strong> — Automatically moves data between tiers based on access patterns.<br>• <strong>S3 Standard-IA</strong> — For infrequently accessed data. Lower storage cost, retrieval fee.<br>• <strong>S3 One Zone-IA</strong> — Like IA but stored in a single AZ. 20% cheaper.<br>• <strong>S3 Glacier Instant Retrieval</strong> — Archive with millisecond access.<br>• <strong>S3 Glacier Flexible Retrieval</strong> — Archive with minutes to hours retrieval.<br>• <strong>S3 Glacier Deep Archive</strong> — Lowest cost. Retrieval in 12-48 hours.</p>',
            'code_example': '# Upload with specific storage class\naws s3 cp backup.tar.gz s3://my-bucket/ \\\n  --storage-class GLACIER\n\n# Check storage class of objects\naws s3api list-objects-v2 \\\n  --bucket my-bucket \\\n  --query "Contents[].{Key:Key,StorageClass:StorageClass}"',
            'code_language': 'bash',
            'tip': 'Use S3 Lifecycle policies to automatically transition objects to cheaper storage classes as they age, saving up to 90% on storage costs.',
            'key_takeaway': 'Choose the right storage class based on access patterns. Use Standard for hot data, IA for warm data, and Glacier for cold archives.',
        },
        {
            'order': 3,
            'title': 'S3 Security & Access Control',
            'section_type': 'best_practice',
            'icon': 'lock',
            'content': '<p>S3 provides multiple layers of access control:</p><p>• <strong>Bucket Policies</strong> — JSON-based policies attached to buckets. Control who can access what.<br>• <strong>IAM Policies</strong> — Attached to users/roles to grant S3 permissions.<br>• <strong>ACLs</strong> — Legacy access control (AWS recommends disabling).<br>• <strong>Block Public Access</strong> — Account and bucket-level settings to prevent public exposure.</p><p><strong>Best practices:</strong></p><p>• Enable <strong>Block Public Access</strong> on all buckets by default<br>• Use <strong>bucket policies</strong> for resource-based access control<br>• Enable <strong>server-side encryption</strong> (SSE-S3 or SSE-KMS)<br>• Enable <strong>access logging</strong> for audit trails<br>• Use <strong>MFA Delete</strong> for critical data</p>',
            'code_example': '# Enable server-side encryption\naws s3api put-bucket-encryption \\\n  --bucket my-bucket \\\n  --server-side-encryption-configuration \\\n  \'{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}\'',
            'code_language': 'bash',
            'tip': 'Always enable "Block Public Access" settings unless you explicitly need public access (like hosting a static website). Data breaches from misconfigured S3 buckets are one of the most common cloud security incidents.',
            'key_takeaway': 'S3 security is multi-layered: use bucket policies, IAM policies, encryption, and Block Public Access to protect your data.',
        },
        {
            'order': 4,
            'title': 'Versioning & Lifecycle Rules',
            'section_type': 'concept',
            'icon': 'history',
            'content': '<p><strong>Versioning</strong> keeps multiple versions of an object in the same bucket. If you overwrite or delete a file, previous versions are preserved.</p><p><strong>Benefits:</strong> Accidental deletion recovery, audit trail, data protection.</p><p><strong>Lifecycle Rules</strong> automate transitioning objects between storage classes or deleting them after a set period:</p><p>• Transition current versions to IA after 30 days<br>• Transition to Glacier after 90 days<br>• Expire (delete) objects after 365 days<br>• Clean up incomplete multipart uploads after 7 days</p>',
            'code_example': '# Enable versioning\naws s3api put-bucket-versioning \\\n  --bucket my-bucket \\\n  --versioning-configuration Status=Enabled\n\n# List object versions\naws s3api list-object-versions \\\n  --bucket my-bucket \\\n  --prefix myfile.txt',
            'code_language': 'bash',
            'tip': 'Once enabled, versioning cannot be disabled — only suspended. Previous versions still exist and incur storage costs. Use lifecycle rules to manage old versions.',
            'key_takeaway': 'Enable versioning for critical buckets to protect against accidental deletions. Use lifecycle rules to optimize storage costs automatically.',
        },
    ]
    StudySection.objects.filter(material=mat).delete()
    for s in sections_data:
        StudySection.objects.create(material=mat, **s)
    print(f"✅ S3 study material seeded: {mat.title}")

# ─── VPC STUDY MATERIAL ────────────────────────────────────────
vpc_lab = Lab.objects.filter(slug='vpc-networking-lab').first()
if vpc_lab:
    mat, created = StudyMaterial.objects.update_or_create(
        lab=vpc_lab,
        defaults={
            'title': 'Amazon VPC - Complete Guide to Virtual Private Cloud',
            'overview': 'Amazon VPC lets you launch AWS resources in a logically isolated virtual network. This guide covers VPC architecture, subnets, route tables, internet gateways, NAT gateways, NACLs, and how all networking components work together to create secure, scalable cloud networks.',
            'icon': 'hub',
            'estimated_read_minutes': 22,
            'prerequisites': 'Basic networking knowledge (IP addresses, CIDR notation, subnets)\nUnderstanding of TCP/IP and routing concepts\nAWS account access (provided in the lab)',
            'learning_outcomes': 'Design and create a custom VPC with public and private subnets\nConfigure route tables for internet and internal traffic\nSet up Internet Gateway and NAT Gateway\nUnderstand NACLs vs Security Groups\nApply VPC networking best practices',
        }
    )
    sections_data = [
        {
            'order': 1,
            'title': 'What is Amazon VPC?',
            'section_type': 'theory',
            'icon': 'lan',
            'content': '<p>Amazon Virtual Private Cloud (VPC) lets you provision a <strong>logically isolated section</strong> of the AWS Cloud where you can launch resources in a virtual network you define.</p><p><strong>Key components:</strong></p><p>• <strong>VPC</strong> — Your isolated virtual network (e.g., 10.0.0.0/16)<br>• <strong>Subnet</strong> — A range of IP addresses within a VPC, tied to an Availability Zone<br>• <strong>Route Table</strong> — Rules that determine where network traffic is directed<br>• <strong>Internet Gateway (IGW)</strong> — Enables internet access for public subnets<br>• <strong>NAT Gateway</strong> — Allows private subnet instances to access the internet without being directly accessible<br>• <strong>NACL</strong> — Network Access Control List, a stateless firewall at the subnet level</p>',
            'code_example': '# Create a VPC\naws ec2 create-vpc \\\n  --cidr-block 10.0.0.0/16 \\\n  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=my-vpc}]"\n\n# Describe your VPCs\naws ec2 describe-vpcs \\\n  --query "Vpcs[].{ID:VpcId,CIDR:CidrBlock,Name:Tags[?Key==\'Name\'].Value|[0]}" \\\n  --output table',
            'code_language': 'bash',
            'tip': 'Every AWS account comes with a default VPC in each region. For production, always create custom VPCs with proper CIDR planning to avoid IP conflicts when connecting multiple VPCs.',
            'key_takeaway': 'A VPC is your private network in AWS. It gives you complete control over IP addressing, subnets, routing, and security.',
        },
        {
            'order': 2,
            'title': 'Subnets - Public vs Private',
            'section_type': 'architecture',
            'icon': 'device_hub',
            'content': '<p>A <strong>subnet</strong> is a range of IP addresses in your VPC. You place AWS resources (like EC2 instances) in subnets.</p><p><strong>Public Subnet:</strong></p><p>• Has a route to an Internet Gateway<br>• Instances can have public IP addresses<br>• Used for: web servers, load balancers, bastion hosts</p><p><strong>Private Subnet:</strong></p><p>• No direct route to the Internet Gateway<br>• Instances are NOT directly accessible from the internet<br>• Used for: databases, application servers, backend services<br>• Can access internet via NAT Gateway (for updates, etc.)</p><p><strong>Best practice:</strong> Use at least 2 Availability Zones with public and private subnets in each for high availability.</p>',
            'code_example': '# Create a public subnet\naws ec2 create-subnet \\\n  --vpc-id vpc-12345 \\\n  --cidr-block 10.0.1.0/24 \\\n  --availability-zone us-east-1a\n\n# Create a private subnet\naws ec2 create-subnet \\\n  --vpc-id vpc-12345 \\\n  --cidr-block 10.0.2.0/24 \\\n  --availability-zone us-east-1a',
            'code_language': 'bash',
            'tip': 'A subnet is not automatically public or private. What makes it public is having a route table entry pointing to an Internet Gateway. The subnet itself is just a CIDR range.',
            'key_takeaway': 'Public subnets route traffic to the Internet Gateway for direct internet access. Private subnets use NAT Gateways for outbound-only internet access.',
        },
        {
            'order': 3,
            'title': 'Route Tables & Gateways',
            'section_type': 'concept',
            'icon': 'route',
            'content': '<p>Every subnet is associated with a <strong>route table</strong> that controls traffic routing.</p><p><strong>Route table for a public subnet:</strong></p><p>• <code>10.0.0.0/16 → local</code> (traffic within VPC)<br>• <code>0.0.0.0/0 → igw-xxxxx</code> (all other traffic → Internet Gateway)</p><p><strong>Route table for a private subnet:</strong></p><p>• <code>10.0.0.0/16 → local</code><br>• <code>0.0.0.0/0 → nat-xxxxx</code> (outbound only via NAT Gateway)</p><p><strong>Internet Gateway (IGW):</strong> Allows communication between your VPC and the internet. One IGW per VPC.</p><p><strong>NAT Gateway:</strong> Allows instances in private subnets to initiate outbound connections to the internet while preventing inbound connections. Placed in a public subnet.</p>',
            'code_example': '# Create and attach Internet Gateway\naws ec2 create-internet-gateway\naws ec2 attach-internet-gateway \\\n  --internet-gateway-id igw-xxxxx \\\n  --vpc-id vpc-12345\n\n# Add route to Internet Gateway\naws ec2 create-route \\\n  --route-table-id rtb-xxxxx \\\n  --destination-cidr-block 0.0.0.0/0 \\\n  --gateway-id igw-xxxxx',
            'code_language': 'bash',
            'tip': 'NAT Gateways are charged hourly plus per-GB of data processed. For development environments, consider using a NAT Instance (t3.micro) to save costs.',
            'key_takeaway': 'Route tables determine where traffic goes. Public subnets point to an IGW, private subnets point to a NAT Gateway for outbound internet access.',
        },
        {
            'order': 4,
            'title': 'NACLs vs Security Groups',
            'section_type': 'concept',
            'icon': 'security',
            'content': '<p>AWS provides two levels of network security:</p><p><strong>Network ACLs (NACLs):</strong></p><p>• Operate at the <strong>subnet level</strong><br>• <strong>Stateless</strong> — return traffic must be explicitly allowed<br>• Support both <strong>allow and deny</strong> rules<br>• Rules are evaluated <strong>in order</strong> (lowest number first)<br>• Apply to ALL instances in the subnet</p><p><strong>Security Groups:</strong></p><p>• Operate at the <strong>instance level</strong><br>• <strong>Stateful</strong> — return traffic is automatically allowed<br>• Support only <strong>allow</strong> rules<br>• ALL rules are evaluated before decision<br>• Apply only to instances assigned to the group</p>',
            'code_example': '# Create a NACL\naws ec2 create-network-acl \\\n  --vpc-id vpc-12345\n\n# Add inbound rule (allow SSH)\naws ec2 create-network-acl-entry \\\n  --network-acl-id acl-xxxxx \\\n  --rule-number 100 \\\n  --protocol tcp \\\n  --port-range From=22,To=22 \\\n  --cidr-block 0.0.0.0/0 \\\n  --rule-action allow \\\n  --ingress',
            'code_language': 'bash',
            'tip': 'Use Security Groups as your primary defense and NACLs as a secondary layer. In most cases, properly configured Security Groups are sufficient.',
            'key_takeaway': 'NACLs are stateless subnet-level firewalls. Security Groups are stateful instance-level firewalls. Use both for defense-in-depth.',
        },
    ]
    StudySection.objects.filter(material=mat).delete()
    for s in sections_data:
        StudySection.objects.create(material=mat, **s)
    print(f"✅ VPC study material seeded: {mat.title}")

print("\n🎉 All study materials seeded successfully!")
