// main.tf

// Sección 1: Configurar el Proveedor de AWS
// Le decimos a Terraform que vamos a trabajar con AWS y en qué región.
// Usará las credenciales que configuraste con "aws configure" en el Paso 0.
provider "aws" {
  region = "us-east-1"
}

// Sección 2: Definir variables para los nombres
// Usar variables hace que nuestro código sea más limpio y fácil de mantener.
variable "project_name" {
  description = "El nombre base para todos los recursos."
  type        = string
  default     = "twittersentiment"
}

// Sección 3: Crear el Stream de Kinesis
// Esta es la tubería por donde pasarán los datos en tiempo real.
// 'shard_count = 1' es para mantenernos en la capa gratuita.
resource "aws_kinesis_stream" "data_stream" {
  name        = "${var.project_name}-stream"
  shard_count = 1

  tags = {
    Project = var.project_name
  }
}

// Sección 4: Crear el Bucket de S3 para datos crudos (RAW)
// Aquí guardaremos una copia de los tweets tal como los recibimos.
resource "aws_s3_bucket" "raw_data_bucket" {
  bucket = "${var.project_name}-raw-data-bucket-${random_id.bucket_suffix.hex}"

  tags = {
    Project = var.project_name
  }
}

// Sección 5: Crear el Bucket de S3 para datos procesados
// Aquí guardaremos los datos después de analizarlos con la IA.
resource "aws_s3_bucket" "processed_data_bucket" {
  bucket = "${var.project_name}-processed-data-bucket-${random_id.bucket_suffix.hex}"

  tags = {
    Project = var.project_name
  }
}

// Sección 6: Configuración de bloqueo de acceso público para los buckets
// Es una buena práctica de seguridad para asegurar que nuestros datos no sean públicos.
resource "aws_s3_bucket_public_access_block" "raw_block" {
  bucket                  = aws_s3_bucket.raw_data_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "processed_block" {
  bucket                  = aws_s3_bucket.processed_data_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


// Sección 7: Generar un sufijo aleatorio para los nombres de los buckets
// Los nombres de los buckets de S3 deben ser únicos a nivel mundial.
// Este recurso añade una cadena aleatoria al final para evitar colisiones.
resource "random_id" "bucket_suffix" {
  byte_length = 8
}


// Sección 8: Salidas (Outputs)
// Esto le dice a Terraform que nos muestre información útil después de crear los recursos.
output "kinesis_stream_name" {
  value       = aws_kinesis_stream.data_stream.name
  description = "El nombre del Kinesis Data Stream creado."
}

output "raw_s3_bucket_name" {
  value       = aws_s3_bucket.raw_data_bucket.bucket
  description = "El nombre del bucket S3 para datos crudos."
}

output "processed_s3_bucket_name" {
  value       = aws_s3_bucket.processed_data_bucket.bucket
  description = "El nombre del bucket S3 para datos procesados."
}
