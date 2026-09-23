# ==============================================================================
# OPSPROBE TERRAFORM SPECIMEN (REVIEWABLE INFRASTRUCTURE AS CODE)
# Vị trí: projects/opsprobe/deploy/terraform/main.tf
#
# LƯU Ý KỸ THUẬT QUAN TRỌNG:
# Máy trạm hiện tại không cài đặt terraform hay aws CLI.
# Tệp này là mã nguồn kiểm tra cú pháp và đối chiếu thiết kế bảo mật
# (reviewable code). Tuyệt đối không tự ý cài đặt và không tạo tài nguyên
# cloud thật để tránh phát sinh chi phí hoặc vi phạm bảo mật.
# ==============================================================================

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

variable "aws_region" {
  type        = string
  description = "AWS region for resources"
  default     = "ap-southeast-1"
}

variable "environment" {
  type        = string
  description = "Target deployment environment"
  default     = "production"
}

variable "github_repo" {
  type        = string
  description = "Full GitHub repository name (owner/repo)"
  default     = "Minhlike/Golang"
}

# Lấy Account ID động của caller hiện tại thay vì hard-code
data "aws_caller_identity" "current" {}

# IAM Trust Policy: Chỉ cấp quyền assume role cho GitHub Actions OIDC
# và bắt buộc khóa chặt vào đúng repository và môi trường cụ thể
data "aws_iam_policy_document" "opsprobe_oidc_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:environment:${var.environment}"]
    }
  }
}

resource "aws_iam_role" "opsprobe_deployer" {
  name               = "opsprobe-deployer-${var.environment}"
  description        = "Least-privilege role for opsprobe CI/CD promotion"
  assume_role_policy = data.aws_iam_policy_document.opsprobe_oidc_assume.json
}

# Phân quyền tối thiểu: chỉ cho phép đẩy ảnh vào repository ECR của opsprobe
resource "aws_iam_policy" "opsprobe_deploy_policy" {
  name        = "opsprobe-deploy-policy-${var.environment}"
  description = "Permissions for opsprobe artifact promotion"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Wildcard * duy nhất được chấp nhận theo ràng buộc của AWS IAM
        # vì ecr:GetAuthorizationToken không hỗ trợ resource-level permissions.
        Sid      = "ECRAuthToken"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = ["*"]
      },
      {
        Sid    = "ECRPushOpsprobe"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = [
          "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/opsprobe"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_deploy" {
  role       = aws_iam_role.opsprobe_deployer.name
  policy_arn = aws_iam_policy.opsprobe_deploy_policy.arn
}
