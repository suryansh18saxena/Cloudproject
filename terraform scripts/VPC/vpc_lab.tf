resource "aws_vpc" "lab_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name      = "lab-vpc-${var.student_id}"
    StudentId = var.student_id
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.lab_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name      = "lab-public-subnet-${var.student_id}"
    StudentId = var.student_id
  }
}

resource "aws_subnet" "private_subnet" {
  vpc_id            = aws_vpc.lab_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name      = "lab-private-subnet-${var.student_id}"
    StudentId = var.student_id
  }
}

resource "aws_internet_gateway" "lab_igw" {
  vpc_id = aws_vpc.lab_vpc.id

  tags = {
    Name      = "lab-igw-${var.student_id}"
    StudentId = var.student_id
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.lab_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lab_igw.id
  }

  tags = {
    Name      = "lab-public-rt-${var.student_id}"
    StudentId = var.student_id
  }
}
