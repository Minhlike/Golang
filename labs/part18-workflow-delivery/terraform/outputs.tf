output "role_arn" {
  description = "ARN of the IAM role to configure in GitHub Actions role-to-assume"
  value       = aws_iam_role.deployer.arn
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider in AWS"
  value       = aws_iam_openid_connect_provider.github.arn
}
