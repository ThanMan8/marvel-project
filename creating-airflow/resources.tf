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
  name               = "airflow-env-marvel"
  environment_class  = "mw1.small"

  network_configuration {
    security_group_ids = [aws_security_group.managed_airflow_sg.id]
    subnet_ids         = [for s in aws_subnet.private : s.id]
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

resource "aws_vpc" "vpc-airflow" {
  cidr_block = var.vpc_cidr_block

  tags = {
  name = "vpc-airflow-dev" }
}

resource "aws_subnet" "private" {
  for_each                = var.private_subnets
  vpc_id                  = aws_vpc.vpc-airflow.id
  cidr_block              = each.value
  availability_zone       = element(data.aws_availability_zones.available.names, index(keys(var.private_subnets), each.key))
  map_public_ip_on_launch = true

  tags = {
    name = "${each.key}-subnet"
  }
}


