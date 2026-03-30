variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "bucket_name" {
  description = "Name of the S3 bucket for Garmin data"
  type        = string
  default     = "garmin-data-bucket"
}

variable "table_name" {
  description = "Name of the DynamoDB table"
  type        = string
  default     = "garmin-activities"
}
