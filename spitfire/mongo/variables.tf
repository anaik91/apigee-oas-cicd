variable "mongodb_uri" {
  type        = string
  description = "MongoDB connection URI"
  # sensitive   = true
}

variable "database_name" {
  type        = string
  description = "Name of the MongoDB database"
}

variable "collections" {
  description = "JSON string representing collections and their index definitions."
  type = map(object({
    indexes = optional(list(object({
      key     = map(number)
      options = object({
        name   = optional(string)
        unique = optional(bool, false)
      })
    })))
  }))
}