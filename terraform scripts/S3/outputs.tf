# 1. IAM User Name
output "iam_user_name" {
  value = aws_iam_user.ec2_launcher.name
}

# 2. AWS Account ID
output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}

# 3. Console Password (Sensitive)
output "console_password" {
  value       = aws_iam_user_login_profile.ec2_user_login.password
  sensitive   = true
}

#Direct Login URL bhi le sakte hain
output "console_login_link" {
  value = "https://${data.aws_caller_identity.current.account_id}.signin.aws.amazon.com/console"
}