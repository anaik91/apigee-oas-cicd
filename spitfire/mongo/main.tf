locals {
  db_qeury = templatefile(
    "${path.module}/db.js",
    {
      mongo_db_name    = var.database_name,
      collections_json = jsonencode(var.collections)
    }
  )
}

resource "local_file" "db" {
  content  = local.db_qeury
  filename = "${path.module}/${var.database_name}.rendered.js"
}

resource "null_resource" "create_mongodb_database" {
  triggers = {
    time = timestamp()
  }

  provisioner "local-exec" {
    command = <<EOT
      mongosh ${var.mongodb_uri} --file "${path.module}/${var.database_name}.rendered.js"
  EOT
  }
}