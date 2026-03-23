resource "aws_iam_user_login_profile" "ec2_user_login" {
  user = aws_iam_user.ec2_launcher.name

  password_length = 12
  password_reset_required = false
}
