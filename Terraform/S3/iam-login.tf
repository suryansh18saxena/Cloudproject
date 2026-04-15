resource "aws_iam_user_login_profile" "s3_user_login" {
  user = aws_iam_user.s3_launcher.name

  password_length = 12
  password_reset_required = false
}
