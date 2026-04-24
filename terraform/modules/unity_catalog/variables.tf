variable "workspace_id" {
  type        = number
  description = "Numeric Databricks workspace ID."
}

variable "catalog_name" {
  type        = string
  description = "Unity Catalog catalog name."
}

variable "schema_names" {
  type        = list(string)
  description = "Schemas created inside the catalog."
}

variable "create_metastore" {
  type        = bool
  description = "Whether Terraform should create the metastore."
  default     = false
}

variable "metastore_name" {
  type        = string
  description = "Metastore name when create_metastore is true."
  default     = "iposto-mlops-metastore"
}

variable "metastore_storage_root" {
  type        = string
  description = "Storage root used by the metastore."
  default     = null
}

variable "existing_metastore_id" {
  type        = string
  description = "Existing metastore ID when create_metastore is false."
  default     = null
}

variable "owner" {
  type        = string
  description = "Optional metastore owner."
  default     = null
}
