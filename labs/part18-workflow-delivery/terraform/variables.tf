variable "github_oidc_subject" {
  description = "Exact sub claim observed for the protected GitHub deployment job; no default because legacy, immutable, and customized subjects differ"
  type        = string

  validation {
    condition     = length(trimspace(var.github_oidc_subject)) > 0 && !strcontains(var.github_oidc_subject, "*")
    error_message = "Supply an exact, non-wildcard OIDC subject verified for the deployment job."
  }
}

variable "github_deploy_ref" {
  description = "Exact Git ref allowed to assume the deployment role"
  type        = string
  default     = "refs/heads/main"
}

variable "ecr_repository_name" {
  description = "Target AWS ECR repository name (must be strictly lowercase alphanumeric, hyphens, underscores, slashes)"
  type        = string
  default     = "golang-master"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-_/]*$", var.ecr_repository_name))
    error_message = "ECR repository name must be strictly lowercase and conform to AWS ECR naming rules."
  }
}

variable "environment" {
  description = "GitHub deployment environment requiring protection gates"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "Target AWS region"
  type        = string
  default     = "ap-southeast-1"
}
