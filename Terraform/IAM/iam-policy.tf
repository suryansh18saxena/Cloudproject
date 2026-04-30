resource "aws_iam_policy" "ec2_launch_policy" {
  name        = "EC2FullControlPolicy-${var.student_id}"
  description = "Allows full control over EC2 for the lab"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:RunInstances",
          "ec2:TerminateInstances",
          "ec2:StopInstances",
          "ec2:StartInstances",
          "ec2:RebootInstances",
          "ec2:CreateKeyPair",
          "ec2:DeleteKeyPair",
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupEgress",
          "ec2:Describe*",
          "ec2:CreateTags"
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