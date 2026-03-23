resource "aws_iam_policy" "ec2_launch_policy" {
  name        = "EC2FullControlPolicy"
  description = "Allows full control over EC2: Create, Manage, and Destroy Instances, Keys, and Security Groups"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # --- 1. Instance Lifecycle (Banana aur Mitana) ---
          "ec2:RunInstances",         # Instance banana
          "ec2:TerminateInstances",   # Instance delete (destroy) karna
          "ec2:StopInstances",        # Instance rokna
          "ec2:StartInstances",       # Instance wapas start karna
          "ec2:RebootInstances",      # Restart karna

          # --- 2. Key Pairs (Apni chaabi khud banana aur delete karna) ---
          "ec2:CreateKeyPair",
          "ec2:DeleteKeyPair",

          # --- 3. Security Groups (Firewall rules set karna) ---
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress", # Rule add karna (e.g., port 22 open)
          "ec2:RevokeSecurityGroupIngress",    # Rule hatana
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupEgress",

          # --- 4. General Viewing Permissions (Sab dekhne ke liye) ---
          "ec2:Describe*",            # Sab kuch list karne ke liye (Images, VPCs, Subnets etc.)
          "ec2:CreateTags"            # Instance par naam/tags lagane ke liye
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "attach_ec2_policy" {
  user       = aws_iam_user.ec2_launcher.name
  policy_arn = aws_iam_policy.ec2_launch_policy.arn
}