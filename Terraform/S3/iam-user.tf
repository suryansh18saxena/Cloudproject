resource "aws_iam_user" "s3_launcher" {
  name = "s3-launch-user-${var.student_id}"

  tags = {
    Purpose = "Launch S3 only"
  }
}

resource "null_resource" "cleanup_trigger" {
  triggers = {
    user_name = aws_iam_user.s3_launcher.name
  }

  provisioner "local-exec" {
    when    = destroy
    # Using 'python' for Windows
    command = "python cleanup_user.py ${self.triggers.user_name}"
  }
}
