resource "aws_iam_user" "vpc_launcher" {
  name = "vpc-launch-user-${var.student_id}"

  tags = {
    Purpose = "Launch VPC only"
  }
}

resource "null_resource" "cleanup_trigger" {
  triggers = {
    user_name = aws_iam_user.vpc_launcher.name
  }

  provisioner "local-exec" {
    when    = destroy
    command = "python cleanup_user.py ${self.triggers.user_name}"
  }
}
