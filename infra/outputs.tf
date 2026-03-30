output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.garmin_data.bucket
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.garmin_activities.name
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.garmin_agent.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.garmin_agent.arn
}
