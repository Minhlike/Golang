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
