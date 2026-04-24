variable "location" {
  type        = string
  description = "Azure region for the Databricks workspace."
}

variable "resource_group_name" {
  type        = string
  description = "Azure resource group name."
}

variable "workspace_name" {
  type        = string
  description = "Azure Databricks workspace name."
}

variable "workspace_sku" {
  type        = string
  description = "Databricks workspace SKU."
  default     = "premium"
}

variable "tags" {
  type        = map(string)
  description = "Default resource tags."
  default = {
    project = "iposto-mlops"
    managed = "terraform"
  }
}
