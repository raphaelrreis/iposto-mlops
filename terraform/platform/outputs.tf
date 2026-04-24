output "catalog_name" {
  value = module.unity_catalog.catalog_name
}

output "cluster_id" {
  value = module.shared_cluster.cluster_id
}

output "training_job_id" {
  value = module.training_job.job_id
}

output "batch_inference_job_id" {
  value = module.batch_inference_job.job_id
}
