variable "name" {
  type        = string
  description = "Databricks job name."
}

variable "task_key" {
  type        = string
  description = "Task key used by the job."
}

variable "existing_cluster_id" {
  type        = string
  description = "Cluster ID used by the job."
}

variable "python_file" {
  type        = string
  description = "Workspace path to the Python task."
}

variable "parameters" {
  type        = list(string)
  description = "Task parameters."
  default     = []
}

variable "max_concurrent_runs" {
  type        = number
  description = "Maximum concurrent job executions."
  default     = 1
}
