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
  description = "Target AWS ECR repository name; validate path segments, separators and API length limits"
  type        = string
  default     = "golang-master"

  validation {
    condition = length(var.ecr_repository_name) >= 2 && length(var.ecr_repository_name) <= 256 && can(regex(
      "^[a-z0-9]+(([._]|__|-+)[a-z0-9]+)*(/[a-z0-9]+(([._]|__|-+)[a-z0-9]+)*)*$", var.ecr_repository_name
    ))
    error_message = "ECR repository name must have valid lowercase path segments and 2-256 characters."
  }
}

variable "deployer_role_name" {
  description = "IAM role name, independent of the repository path; 1-64 IAM-safe characters"
  type        = string
  default     = "golang-master-production-deployer"

  validation {
    condition     = can(regex("^[A-Za-z0-9+=,.@_-]{1,64}$", var.deployer_role_name))
    error_message = "Supply an IAM role name of 1-64 supported characters, without slashes."
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
