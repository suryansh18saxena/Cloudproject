resource "aws_iam_policy" "s3_launch_policy" {
  name        = "S3LabPolicy-${var.student_id}"
  description = "Allows control over S3 for the lab"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "attach_s3_policy" {
  user       = aws_iam_user.s3_launcher.name
  policy_arn = aws_iam_policy.s3_launch_policy.arn
}