output "postgres_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  sensitive   = true
}

output "audio_bucket_name" {
  description = "S3 bucket for audio files"
  value       = aws_s3_bucket.audio.id
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}
