import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'Cloud_Project.settings'
django.setup()

from Lab.models import Lab

lab, created = Lab.objects.get_or_create(
    slug='ec2-launch-lab',
    defaults={
        'title': 'EC2 Instance Launch Lab',
        'description': 'Learn how to launch and configure an EC2 instance with proper security settings on AWS. You will create a security group, launch an instance, and verify it is running.',
        'difficulty': 'beginner',
        'duration_minutes': 60,
        'max_score': 100,
    }
)
print(f'Lab {"created" if created else "already exists"}: {lab.title} (slug={lab.slug})')
