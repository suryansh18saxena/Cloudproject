resource "aws_iam_user" "ec2_launcher" {
  name = "ec2-launch-user"

  tags = {
    Purpose = "Launch EC2 only"
  }
}
  resource "null_resource" "cleanup_trigger" {
  
  triggers = {
    user_name = aws_iam_user.ec2_launcher.name
  }

  provisioner "local-exec" {
    when    = destroy
    # Windows ke liye 'python3' ki jagah sirf 'python' likhein
    command = "python cleanup_user.py ${self.triggers.user_name}"
  }
}

