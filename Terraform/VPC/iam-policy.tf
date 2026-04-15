resource "aws_iam_policy" "vpc_launch_policy" {
  name        = "VPCLabPolicy-${var.student_id}"
  description = "Allows control over VPC for the lab"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateVpc",
          "ec2:DeleteVpc",
          "ec2:DescribeVpcs",
          "ec2:CreateSubnet",
          "ec2:DeleteSubnet",
          "ec2:DescribeSubnets",
          "ec2:CreateInternetGateway",
          "ec2:AttachInternetGateway",
          "ec2:DetachInternetGateway",
          "ec2:DeleteInternetGateway",
          "ec2:DescribeInternetGateways",
          "ec2:CreateRouteTable",
          "ec2:CreateRoute",
          "ec2:AssociateRouteTable",
          "ec2:DeleteRouteTable",
          "ec2:DescribeRouteTables",
          "ec2:DeleteRoute",
          "ec2:DisassociateRouteTable",
          "ec2:CreateTags",
          "ec2:DescribeTags",
          "ec2:ModifyVpcAttribute"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "attach_vpc_policy" {
  user       = aws_iam_user.vpc_launcher.name
  policy_arn = aws_iam_policy.vpc_launch_policy.arn
}