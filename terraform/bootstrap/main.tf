module "databricks_workspace" {
  source              = "../modules/databricks_workspace"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_name      = var.workspace_name
  sku                 = var.workspace_sku
  tags                = var.tags
}
