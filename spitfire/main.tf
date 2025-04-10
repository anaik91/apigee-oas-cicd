module "mongo_db_1" {
  source        = "./mongo"
  mongodb_uri   = "mongodb+srv://<user>:<password>@cluster0.anvtysk.mongodb.net/"
  database_name = "engine-iac"
  collections = {
    "engine_state_instructions" : {
      "indexes" : [
        {
          "key" : { "cloudCustomerId" : 1 },
          "options" : { "name" : "cloudCustomerId" }
        },
        {
          "key" : {"_ftsx": 1 },
          "options" : { "name" : "iac"}
        }
      ]
    },
    "engine_execution_state" : {
      "indexes" : [
        {
          "key" : { "cloudCustomerId" : 1 },
          "options" : { "name" : "cloudCustomerId" }
        },
        {
          "key" : { "executionId" : 1 },
          "options" : { "name" : "executionId", "unique" : true }
        }
      ]
    }
  }
}