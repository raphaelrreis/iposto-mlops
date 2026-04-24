variable "location" {
  type        = string
  description = "Azure region for the Databricks workspace."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group that hosts the Databricks workspace."
}

variable "workspace_name" {
  type        = string
  description = "Name of the Azure Databricks workspace."
}

variable "sku" {
  type        = string
  description = "Workspace pricing tier."
  default     = "premium"
}

variable "tags" {
  type        = map(string)
  description = "Standard resource tags."
  default     = {}
}
