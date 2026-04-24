output "catalog_name" {
  value = databricks_catalog.this.name
}

output "schema_names" {
  value = [for schema in databricks_schema.this : schema.name]
}

output "metastore_id" {
  value = local.metastore_id
}
