import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'Cloud_Project.settings'
django.setup()

from Lab.models import Lab

labs_data = [
    {
        'slug': 'ec2-launch-lab',
        'title': 'EC2 Instance Launch Lab',
        'description': 'Learn how to launch and configure an EC2 instance on AWS.',
        'difficulty': 'beginner',
        'terraform_dir': 'Terraform/IAM'
    },
    {
        'slug': 's3-bucket-lab',
        'title': 'S3 Architecture Lab',
        'description': 'Securely configure an S3 bucket with versioning, policies, and blocking public access.',
        'difficulty': 'beginner',
        'terraform_dir': 'Terraform/S3'
    },
    {
        'slug': 'vpc-networking-lab',
        'title': 'VPC Networking Lab',
        'description': 'Construct a custom VPC with subnets, internet gateways, and route tables.',
        'difficulty': 'intermediate',
        'terraform_dir': 'Terraform/VPC'
    }
]

for l in labs_data:
    lab, created = Lab.objects.update_or_create(
        slug=l['slug'],
        defaults={
            'title': l['title'],
            'description': l['description'],
            'difficulty': l['difficulty'],
            'duration_minutes': 60,
            'max_score': 100,
            'terraform_dir': l['terraform_dir'],
        }
    )
    print(f'Lab {"created" if created else "updated"}: {lab.title} (slug={lab.slug})')
