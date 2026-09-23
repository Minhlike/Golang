variable "github_org" {
  description = "GitHub organization or username owner of repository"
  type        = string
  default     = "Minhlike"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "Golang"
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
