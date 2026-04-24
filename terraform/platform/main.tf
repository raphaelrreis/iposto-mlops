module "shared_cluster" {
  source                  = "../modules/cluster"
  cluster_name            = var.cluster_name
  spark_version           = var.spark_version
  node_type_id            = var.node_type_id
  num_workers             = var.num_workers
  autotermination_minutes = var.autotermination_minutes
  docker_image            = var.docker_image
  tags                    = var.tags
}

module "unity_catalog" {
  source                 = "../modules/unity_catalog"
  workspace_id           = var.workspace_id
  catalog_name           = var.catalog_name
  schema_names           = var.schema_names
  create_metastore       = var.create_metastore
  metastore_name         = var.metastore_name
  metastore_storage_root = var.metastore_storage_root
  existing_metastore_id  = var.existing_metastore_id
}

module "training_job" {
  source              = "../modules/job"
  name                = "iposto-mlops-train-model"
  task_key            = "train_model"
  existing_cluster_id = module.shared_cluster.cluster_id
  python_file         = var.training_python_file
  parameters          = var.training_job_parameters
}

module "batch_inference_job" {
  source              = "../modules/job"
  name                = "iposto-mlops-batch-inference"
  task_key            = "batch_inference"
  existing_cluster_id = module.shared_cluster.cluster_id
  python_file         = var.batch_python_file
  parameters          = var.batch_job_parameters
}
