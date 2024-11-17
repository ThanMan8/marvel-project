resource "aws_s3_bucket" "managed-airflow-bucket" {
  bucket        = var.s3_bucket_name
  force_destroy = "false"

  tags = {
    Name = "airflow-bucket-marvel"
  }
}

resource "aws_s3_bucket_versioning" "managed-airflow-bucket-versioning" {
  bucket = aws_s3_bucket.managed-airflow-bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Create the `dags/` subfolder in the S3 bucket
resource "aws_s3_object" "dags_folder" {
  bucket  = aws_s3_bucket.managed-airflow-bucket.id
  key     = "dags/" # Creates the folder
  content = ""      # Empty content to simulate a folder
}

resource "aws_s3_bucket" "data_upload_bucket" {
  bucket        = "my-upload-data-bucket"
  force_destroy = false

  tags = {
    Name = "data-upload-bucket"
  }
}

resource "aws_s3_bucket_versioning" "data_upload_bucket_versioning" {
  bucket = aws_s3_bucket.data_upload_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}
