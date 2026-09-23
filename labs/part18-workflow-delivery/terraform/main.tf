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
  name               = "github-actions-${var.github_repo}-${var.environment}-deployer"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Purpose     = "Least-privilege CI/CD deployment"
  }
}

# 4. Permissions Policy: Đặc quyền tối thiểu (Least Privilege)
# Không dùng Action: "*", không Resource: "*". Chỉ cấp quyền cần thiết để nạp image và cập nhật service.
data "aws_iam_policy_document" "deploy_permissions" {
  statement {
    sid    = "ECRAuthToken"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
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
    # Khóa vào repository cụ thể thay vì mọi repo trong account
    resources = [
      "arn:aws:ecr:${var.aws_region}:*:repository/${var.github_repo}"
    ]
  }

  statement {
    sid    = "AppRunnerServiceUpdate"
    effect = "Allow"
    actions = [
      "apprunner:StartDeployment",
      "apprunner:DescribeService"
    ]
    # Khóa vào service cụ thể thay vì toàn bộ account
    resources = [
      "arn:aws:apprunner:${var.aws_region}:*:service/${var.github_repo}-${var.environment}/*"
    ]
  }
}

resource "aws_iam_role_policy" "deploy_policy" {
  name   = "deploy-permissions"
  role   = aws_iam_role.deployer.id
  policy = data.aws_iam_policy_document.deploy_permissions.json
}
