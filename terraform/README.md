# Terraform Layout

The Terraform code is intentionally split into two phases:

1. `bootstrap/`
   - Creates the Azure resource group and Databricks workspace.
2. `platform/`
   - Configures cluster, Unity Catalog objects and baseline Databricks jobs inside an existing workspace.

This split avoids coupling the Databricks provider to a workspace that does not exist yet at plan time.
