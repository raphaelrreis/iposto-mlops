variable "databricks_host" {
  type        = string
  description = "Databricks workspace host."
}

variable "databricks_token" {
  type        = string
  description = "PAT used by Terraform to configure Databricks."
  sensitive   = true
}

variable "workspace_id" {
  type        = number
  description = "Numeric workspace ID used for Unity Catalog assignment."
}

variable "cluster_name" {
  type        = string
  description = "Shared MLOps cluster name."
  default     = "iposto-mlops-ml-cluster"
}

variable "spark_version" {
  type        = string
  description = "Databricks runtime used by the shared cluster."
  default     = "14.3.x-cpu-ml-scala2.12"
}

variable "node_type_id" {
  type        = string
  description = "Databricks node type."
  default     = "Standard_DS3_v2"
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

variable "docker_image" {
  type        = string
  description = "DCS image URL."
  default     = "ghcr.io/your-org/iposto-mlops:latest"
}

variable "catalog_name" {
  type        = string
  description = "Unity Catalog catalog name."
  default     = "iposto_mlops"
}

variable "schema_names" {
  type        = list(string)
  description = "Schemas to create."
  default     = ["bronze", "silver", "gold", "ml"]
}

variable "create_metastore" {
  type        = bool
  description = "Whether to create a new metastore."
  default     = false
}

variable "metastore_name" {
  type        = string
  description = "Metastore name."
  default     = "iposto-mlops-metastore"
}

variable "metastore_storage_root" {
  type        = string
  description = "Storage root for a new metastore."
  default     = null
}

variable "existing_metastore_id" {
  type        = string
  description = "Existing metastore ID."
  default     = null
}

variable "training_python_file" {
  type        = string
  description = "Workspace file path for the training task."
  default     = "/Workspace/Shared/iposto-mlops/databricks_assets/jobs/train_model.py"
}

variable "training_job_parameters" {
  type        = list(string)
  description = "Parameters for the training job."
  default = [
    "--input-path",
    "dbfs:/Volumes/iposto_mlops/fuelops/gold/fuel_price_features",
    "--input-format",
    "delta",
  ]
}

variable "batch_python_file" {
  type        = string
  description = "Workspace file path for the batch inference task."
  default     = "/Workspace/Shared/iposto-mlops/databricks_assets/jobs/batch_inference.py"
}

variable "batch_job_parameters" {
  type        = list(string)
  description = "Parameters for the batch inference job."
  default = [
    "--input-path",
    "dbfs:/Volumes/iposto_mlops/fuelops/gold/fuel_price_features",
    "--output-path",
    "dbfs:/Volumes/iposto_mlops/fuelops/gold/predictions",
    "--model-uri",
    "models:/iposto_mlops_next_day_price/Staging",
    "--input-format",
    "delta",
    "--output-format",
    "delta",
  ]
}

variable "tags" {
  type        = map(string)
  description = "Default tags applied to Databricks assets."
  default = {
    project = "iposto-mlops"
    managed = "terraform"
  }
}
