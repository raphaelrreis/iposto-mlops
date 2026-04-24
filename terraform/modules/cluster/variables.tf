variable "cluster_name" {
  type        = string
  description = "Human-readable cluster name."
}

variable "spark_version" {
  type        = string
  description = "Databricks runtime version."
}

variable "node_type_id" {
  type        = string
  description = "Databricks node type."
}

variable "num_workers" {
  type        = number
  description = "Number of worker nodes."
  default     = 2
}

variable "autotermination_minutes" {
  type        = number
  description = "Cluster auto-termination in minutes."
  default     = 30
}

variable "data_security_mode" {
  type        = string
  description = "Databricks security mode."
  default     = "SINGLE_USER"
}

variable "docker_image" {
  type        = string
  description = "Optional DCS image URL."
  default     = null
}

variable "spark_conf" {
  type        = map(string)
  description = "Optional Spark configuration."
  default     = {}
}

variable "tags" {
  type        = map(string)
  description = "Cluster custom tags."
  default     = {}
}
