##################################################################################
# VARIABLES
##################################################################################

variable "region" {
  type        = string
  description = "(Optional) AWS Region to use. Default: us-east-1"
  default     = "us-east-1"
}

variable "account_id" {
  type        = string
  description = "(Required) Billing code for network resources"
  default     = "1689-8709-7870"
}

variable "name" {
  type        = string
  description = "(Required) Environment for identification"
  default     = "dev"
}

variable "s3_bucket_name" {
  type        = string
  description = "This is the name of bucket"
  default     = "airflow-bucket-marvel"
}

variable "vpc_cidr_block" {
  type        = string
  description = "Base CIDR Block for VPC"
  default     = "10.192.0.0/16"
}

variable "private_subnets" {
  type = map(string)
  default = {
    private-1 = "10.192.20.0/24"
    private-2 = "10.192.21.0/24"
  }
}

variable "public_subnets" {
  type = map(string)
  default = {
    public-1 = "10.192.10.0/24"
    public-2 = "10.192.11.0/24"
  }
}
