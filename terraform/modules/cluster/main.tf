resource "databricks_cluster" "this" {
  cluster_name            = var.cluster_name
  spark_version           = var.spark_version
  node_type_id            = var.node_type_id
  num_workers             = var.num_workers
  autotermination_minutes = var.autotermination_minutes
  data_security_mode      = var.data_security_mode
  spark_conf              = var.spark_conf
  custom_tags             = var.tags

  dynamic "docker_image" {
    for_each = var.docker_image == null ? [] : [var.docker_image]
    content {
      url = docker_image.value
    }
  }
}
