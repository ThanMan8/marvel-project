[1mdiff --git a/creating-airflow/resources.tf b/creating-airflow/resources.tf[m
[1mindex f9f2488..e8d97ef 100644[m
[1m--- a/creating-airflow/resources.tf[m
[1m+++ b/creating-airflow/resources.tf[m
[36m@@ -80,7 +80,7 @@[m [mresource "aws_vpc" "vpc-airflow" {[m
   cidr_block = var.vpc_cidr_block[m
 [m
   tags = {[m
[31m-    name = "vpc-airflow-dev" }[m
[32m+[m[32m  name = "vpc-airflow-dev" }[m
 }[m
 [m
 resource "aws_subnet" "private" {[m
