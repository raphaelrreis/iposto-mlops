resource "databricks_job" "this" {
  name                = var.name
  max_concurrent_runs = var.max_concurrent_runs

  task {
    task_key            = var.task_key
    existing_cluster_id = var.existing_cluster_id

    spark_python_task {
      python_file = var.python_file
      parameters  = var.parameters
    }
  }
}
