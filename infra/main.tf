provider "aws" {
  region = var.aws_region
}

# Bucket S3 para armazenar dados Garmin
resource "aws_s3_bucket" "garmin_data" {
  bucket = var.bucket_name

  tags = {
    Name        = "Garmin Data Bucket"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "garmin_data" {
  bucket = aws_s3_bucket.garmin_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Tabela DynamoDB para metadados de atividades
resource "aws_dynamodb_table" "garmin_activities" {
  name           = var.table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "activityId"

  attribute {
    name = "activityId"
    type = "S"
  }

  attribute {
    name = "startTimeLocal"
    type = "S"
  }

  global_secondary_index {
    name            = "StartTimeIndex"
    hash_key        = "startTimeLocal"
    projection_type = "ALL"
  }

  tags = {
    Name        = "Garmin Activities"
    Environment = var.environment
  }
}

# Lambda Function
resource "aws_lambda_function" "garmin_agent" {
  function_name = "garmin-aws-agent"
  runtime       = "python3.11"
  handler       = "index.lambda_handler"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 30
  memory_size   = 256

  filename         = "lambda/function.zip"
  source_code_hash = filebase64sha256("lambda/function.zip")

  environment {
    variables = {
      GARMIN_BUCKET_NAME = aws_s3_bucket.garmin_data.bucket
      GARMIN_TABLE_NAME  = aws_dynamodb_table.garmin_activities.name
      LOG_LEVEL          = "INFO"
    }
  }

  tags = {
    Name        = "Garmin AWS Agent"
    Environment = var.environment
  }
}

# IAM Role para Lambda
resource "aws_iam_role" "lambda_role" {
  name = "garmin-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "garmin-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.garmin_data.arn,
          "${aws_s3_bucket.garmin_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.garmin_activities.arn
      }
    ]
  })
}
