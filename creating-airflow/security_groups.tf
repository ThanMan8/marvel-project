##################################################################################
# RESOURCES
##################################################################################

resource "aws_security_group" "managed_airflow_sg" {
  name   = "managed_airflow-sg"
  vpc_id = aws_vpc.vpc-airflow.id

  tags = {
    Name = "managed-airflow-sg"
  }
}

##### Security group rules
resource "aws_security_group_rule" "allow_all_out_traffic_managed_airflow" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = -1
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.managed_airflow_sg.id
}

resource "aws_security_group_rule" "allow_inbound_internal_traffic" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.managed_airflow_sg.id
}

resource "aws_security_group_rule" "self_reference_sgr" {
  type              = "ingress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  self              = true
  security_group_id = aws_security_group.managed_airflow_sg.id
}