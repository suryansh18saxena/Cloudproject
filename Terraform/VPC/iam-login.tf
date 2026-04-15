resource "aws_iam_user_login_profile" "vpc_user_login" {
  user = aws_iam_user.vpc_launcher.name

  password_length = 12
  password_reset_required = false
}
