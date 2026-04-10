resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "lab_bucket" {
  bucket        = "lab-bucket-${var.student_id}-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = {
    Name      = "lab-bucket-${var.student_id}"
    StudentId = var.student_id
  }
}

resource "aws_s3_bucket_versioning" "lab_bucket_versioning" {
  bucket = aws_s3_bucket.lab_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}
