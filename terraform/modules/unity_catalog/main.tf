resource "databricks_metastore" "this" {
  count        = var.create_metastore ? 1 : 0
  name         = var.metastore_name
  storage_root = var.metastore_storage_root
  owner        = var.owner
}

locals {
  metastore_id = var.create_metastore ? databricks_metastore.this[0].id : var.existing_metastore_id
}

resource "databricks_metastore_assignment" "workspace" {
  workspace_id         = var.workspace_id
  metastore_id         = local.metastore_id
  default_catalog_name = var.catalog_name
}

resource "databricks_catalog" "this" {
  name         = var.catalog_name
  metastore_id = local.metastore_id
  comment      = "Managed catalog for iposto-mlops."
}

resource "databricks_schema" "this" {
  for_each     = toset(var.schema_names)
  catalog_name = databricks_catalog.this.name
  name         = each.value
  comment      = "Managed schema for iposto-mlops."
}
