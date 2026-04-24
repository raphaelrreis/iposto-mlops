# Deployment Notes

The runnable GitHub Actions workflows live in `.github/workflows/`.

Expected repository secrets and variables:

- `AZURE_CREDENTIALS`
- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`
- `vars.AZURE_LOCATION`
- `vars.AZURE_DATABRICKS_RG`
- `vars.AZURE_DATABRICKS_WORKSPACE`
- `vars.DATABRICKS_WORKSPACE_ID`

Operational sequence:

1. Apply `terraform/bootstrap` to create the workspace.
2. Build and push the immutable Docker image for DCS.
3. Apply `terraform/platform` to configure the workspace.
4. Deploy the Databricks Asset Bundle.
