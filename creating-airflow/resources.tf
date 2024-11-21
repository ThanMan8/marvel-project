##################################################################################
# PROVIDERS
##################################################################################
provider "aws" {
  region = var.region
}

##################################################################################
# DATA
##################################################################################
data "aws_availability_zones" "available" {}

##################################################################################
# RESOURCES
##################################################################################

# VPC Resource
resource "aws_vpc" "vpc-airflow" {
  cidr_block = var.vpc_cidr_block

  tags = {
    name = "vpc-airflow-dev"
  }
}

# Public Subnet (for internet access)
resource "aws_subnet" "public" {
  for_each                = var.public_subnets
  vpc_id                  = aws_vpc.vpc-airflow.id
  cidr_block              = each.value
  availability_zone       = element(data.aws_availability_zones.available.names, index(keys(var.public_subnets), each.key))
  map_public_ip_on_launch = true

  tags = {
    name = "${each.key}-subnet"
  }
}

# Private Subnets (for internal resources like MWAA)
resource "aws_subnet" "private" {
  for_each                = var.private_subnets
  vpc_id                  = aws_vpc.vpc-airflow.id
  cidr_block              = each.value
  availability_zone       = element(data.aws_availability_zones.available.names, index(keys(var.private_subnets), each.key))
  map_public_ip_on_launch = false

  tags = {
    name = "${each.key}-subnet"
  }
}

# Create Internet Gateway (IGW) for public internet access
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc-airflow.id

  tags = {
    Name = "igw-airflow-vpc"
  }
}

# Create Route Table for Public Subnet (Internet access)
resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.vpc-airflow.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "public-route-table"
  }
}

# Associate Route Table with Public Subnet
resource "aws_route_table_association" "public_subnet_association" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public_route_table.id
}

# MWAA Environment Resource
resource "aws_mwaa_environment" "managed_airflow" {
  airflow_version = "2.10.1"
  airflow_configuration_options = {
    "core.load_default_connections"   = "false"
    "core.dag_file_processor_timeout" = 150
    "core.dagbag_import_timeout"      = 90
    "core.load_examples"              = "false"
  }

  dag_s3_path        = "dags/" #(checking in s3 bucket airflow the file dags/) 
  execution_role_arn = aws_iam_role.role.arn
  name               = "airflow-marvel"
  environment_class  = "mw1.small"

  network_configuration {
    security_group_ids = [aws_security_group.managed_airflow_sg.id]
    subnet_ids         = [for s in aws_subnet.public : s.id] # Use both public subnets
  }

  source_bucket_arn               = aws_s3_bucket.managed-airflow-bucket.arn
  weekly_maintenance_window_start = "SUN:19:00"

  logging_configuration {
    dag_processing_logs {
      enabled   = true
      log_level = "WARNING"
    }

    scheduler_logs {
      enabled   = true
      log_level = "WARNING"
    }

    task_logs {
      enabled   = true
      log_level = "WARNING"
    }

    webserver_logs {
      enabled   = true
      log_level = "WARNING"
    }

    worker_logs {
      enabled   = true
      log_level = "WARNING"
    }
  }

  tags = {
    name = "airflow-dev-marvel"
  }

  lifecycle {
    ignore_changes = [
      requirements_s3_object_version,
      plugins_s3_object_version,
    ]
  }
}
