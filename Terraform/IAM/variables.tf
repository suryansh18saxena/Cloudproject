variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "student_id" {
  description = "Student ID or username for the lab session"
  type        = string
}
