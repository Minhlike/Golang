terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Lấy thông tin AWS Account ID của caller hiện tại để khóa chặt ARN tài nguyên
data "aws_caller_identity" "current" {}

# 1. GitHub OIDC Identity Provider
# Cho phép AWS xác thực chữ ký số từ token do GitHub Actions cấp phát
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1", "1c58a3a8518e8759bf075b76b750d4f2df264fcd"]
}

# 2. Trust Policy: Khóa chặt repo và environment
# Chỉ job có claim `repo:org/repo:environment:production` mới có thể assume role
data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      # Khóa chặt repository và environment cụ thể
      values   = ["repo:${var.github_org}/${var.github_repo}:environment:${var.environment}"]
    }
  }
}

# 3. IAM Role cho deployment job
resource "aws_iam_role" "deployer" {
  name               = "github-actions-${var.ecr_repository_name}-${var.environment}-deployer"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Purpose     = "Least-privilege CI/CD deployment"
  }
}

# 4. Permissions Policy: Đặc quyền tối thiểu (Least Privilege)
# Lưu ý về wildcard: AWS action ecr:GetAuthorizationToken bắt buộc Resource = "*",
# vì AWS IAM không hỗ trợ phân quyền ở cấp độ tài nguyên cho action này.
# Ngược lại, mọi permission có hỗ trợ resource-level đều phải được khóa hẹp vào
# đúng account ID và tên tài nguyên cụ thể.
data "aws_iam_policy_document" "deploy_permissions" {
  statement {
    sid    = "ECRAuthToken"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
    # Bắt buộc của AWS IAM: action này không hỗ trợ resource scoping
    resources = ["*"]
  }

  statement {
    sid    = "ECRPushAndInspect"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]
    # Khóa chặt vào Account ID và ECR Repository cụ thể
    resources = [
      "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/${var.ecr_repository_name}"
    ]
  }

  statement {
    sid    = "AppRunnerServiceUpdate"
    effect = "Allow"
    actions = [
      "apprunner:StartDeployment",
      "apprunner:DescribeService"
    ]
    # Khóa chặt vào Account ID và Service cụ thể
    resources = [
      "arn:aws:apprunner:${var.aws_region}:${data.aws_caller_identity.current.account_id}:service/${var.ecr_repository_name}-${var.environment}/*"
    ]
  }
}

resource "aws_iam_role_policy" "deploy_policy" {
  name   = "deploy-permissions"
  role   = aws_iam_role.deployer.id
  policy = data.aws_iam_policy_document.deploy_permissions.json
}
