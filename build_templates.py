import re


with open('templates/lab/EC2_lab.html', 'r', encoding='utf-8') as f:
    ec2_html = f.read()

# For S3
s3_html = ec2_html.replace('EC2 Instance Launch Lab', 'S3 Architecture Lab')
s3_html = s3_html.replace('Learn how to launch and configure an EC2 instance with proper security settings on AWS.', 'Learn how to securely configure an S3 bucket with versioning, policies, and block public access.')
s3_html = s3_html.replace('By the end of this lab, you will be able to launch an EC2 instance in a specified region, configure a security group to allow inbound SSH access, and verify that the instance is running correctly.', 'By the end of this lab, you will be able to launch an S3 bucket, enable versioning, configure bucket policies, block public access, and upload objects successfully.')

s3_steps = """
            <div class="steps-container">
                <article class="step-card active" id="step-1">
                    <header class="step-header">
                        <div class="step-info"><span class="step-number">1</span><h3 class="step-title-text">Create S3 Bucket</h3></div>
                        <span class="expand-icon material-symbols-outlined">expand_more</span>
                    </header>
                    <div class="step-body">
                        <p>Navigate to S3. Click Create Bucket. Name it securely. You must create it in the us-east-1 region.</p>
                    </div>
                </article>
                <article class="step-card" id="step-2">
                    <header class="step-header">
                        <div class="step-info"><span class="step-number">2</span><h3 class="step-title-text">Enable Versioning</h3></div>
                        <span class="expand-icon material-symbols-outlined">expand_more</span>
                    </header>
                    <div class="step-body"><p>Go to the Properties tab of your bucket and Edit Bucket Versioning to Enable it.</p></div>
                </article>
                <article class="step-card" id="step-3">
                    <header class="step-header">
                        <div class="step-info"><span class="step-number">3</span><h3 class="step-title-text">Configure Policy & Block Public Access</h3></div>
                        <span class="expand-icon material-symbols-outlined">expand_more</span>
                    </header>
                    <div class="step-body"><p>Ensure Block Public Access is turned ON. Then attach a basic bucket policy allowing your IAM user.</p></div>
                </article>
                <article class="step-card" id="step-4">
                    <header class="step-header">
                        <div class="step-info"><span class="step-number">4</span><h3 class="step-title-text">Upload an Object</h3></div>
                        <span class="expand-icon material-symbols-outlined">expand_more</span>
                    </header>
                    <div class="step-body"><p>Upload any file to your newly created S3 bucket to test the configuration.</p></div>
                </article>
            </div>
"""

vpc_html = ec2_html.replace('EC2 Instance Launch Lab', 'VPC Networking Lab')
vpc_html = vpc_html.replace('Learn how to launch and configure an EC2 instance with proper security settings on AWS.', 'Learn how to construct a custom VPC with subnets, internet gateways, and route tables.')
vpc_html = vpc_html.replace('By the end of this lab, you will be able to launch an EC2 instance in a specified region, configure a security group to allow inbound SSH access, and verify that the instance is running correctly.', 'By the end of this lab, you will be able to create a VPC, attach an Internet Gateway, create subnets, configure route tables, and associate them properly.')

vpc_steps = """
            <div class="steps-container">
                <article class="step-card active" id="step-1">
                    <header class="step-header">
                        <div class="step-info"><span class="step-number">1</span><h3 class="step-title-text">Create VPC and Subnets</h3></div>
                        <span class="expand-icon material-symbols-outlined">expand_more</span>
                    </header>
                    <div class="step-body">
                        <p>Navigate to the VPC console. Create a new VPC (e.g., 10.0.0.0/16). Then create at least 2 subnets inside this VPC.</p>
                    </div>
                </article>
                <article class="step-card" id="step-2">
                    <header class="step-header">
                        <div class="step-info"><span class="step-number">2</span><h3 class="step-title-text">Attach Internet Gateway</h3></div>
                        <span class="expand-icon material-symbols-outlined">expand_more</span>
                    </header>
                    <div class="step-body"><p>Create an Internet Gateway and attach it to your newly created VPC.</p></div>
                </article>
                <article class="step-card" id="step-3">
                    <header class="step-header">
                        <div class="step-info"><span class="step-number">3</span><h3 class="step-title-text">Configure Route Tables</h3></div>
                        <span class="expand-icon material-symbols-outlined">expand_more</span>
                    </header>
                    <div class="step-body"><p>Create a custom Route Table for your VPC. Edit the routes to point 0.0.0.0/0 to the Internet Gateway.</p></div>
                </article>
                <article class="step-card" id="step-4">
                    <header class="step-header">
                        <div class="step-info"><span class="step-number">4</span><h3 class="step-title-text">Associate Subnets</h3></div>
                        <span class="expand-icon material-symbols-outlined">expand_more</span>
                    </header>
                    <div class="step-body"><p>Associate your public subnets with the newly created Route Table to grant them internet access.</p></div>
                </article>
            </div>
"""

s3_pattern = re.compile(r'<div class="steps-container">.*?</div>\s*<div class="progress-wrapper">', re.DOTALL)
s3_final = s3_pattern.sub(s3_steps + '\n            <div class="progress-wrapper">', s3_html)

vpc_pattern = re.compile(r'<div class="steps-container">.*?</div>\s*<div class="progress-wrapper">', re.DOTALL)
vpc_final = vpc_pattern.sub(vpc_steps + '\n            <div class="progress-wrapper">', vpc_html)

with open('templates/lab/s3_lab.html', 'w', encoding='utf-8') as f:
    f.write(s3_final)

with open('templates/lab/vpc_lab.html', 'w', encoding='utf-8') as f:
    f.write(vpc_final)
