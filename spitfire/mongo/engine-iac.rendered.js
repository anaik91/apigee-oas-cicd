// Script to manage MongoDB collections and indexes (create and delete)

dbName = "engine-iac";
collections_json = '{"engine_execution_state":{"indexes":[{"key":{"cloudCustomerId":1},"options":{"name":"cloudCustomerId","unique":false}},{"key":{"executionId":1},"options":{"name":"executionId","unique":true}}]},"engine_state_instructions":{"indexes":[{"key":{"cloudCustomerId":1},"options":{"name":"cloudCustomerId","unique":false}},{"key":{"_ftsx":1},"options":{"name":"iac","unique":false}}]}}';

try {
    collections_config = JSON.parse(collections_json);
} catch (e) {
    print("Error parsing collections_json: " + e);
    quit(1);  // Exit the script with an error
}

print("Collections Configuration:", collections_config);

db = db.getSiblingDB(dbName);

dbNames = db.adminCommand({ listDatabases: 1 }).databases.map(db => db.name);

if (!dbNames.includes(dbName)) {
    print("Database '" + dbName + "' created successfully.");
} else {
    print("Database '" + dbName + "' already exists.");
}

existing_collections = db.getCollectionNames();
print("Existing collections:", existing_collections);

// --- Collection Management ---
for (let collection_name in collections_config) {
    if (!collections_config.hasOwnProperty(collection_name)) continue; // Skip inherited properties

    let collection_config = collections_config[collection_name];

    if (!existing_collections.includes(collection_name)) {
        print("Creating Collection: " + collection_name);
        try {
            db.createCollection(collection_name);
        } catch (e) {
            print("Error creating collection " + collection_name + ": " + e);
        }
    } else {
        print("Collection '" + collection_name + "' already exists.");
    }

    // --- Index Management ---
    if (collection_config.indexes) {
        let desired_indexes = collection_config.indexes;
        let existing_indexes = db.getCollection(collection_name).getIndexes().map(idx => idx.name);
        print("Existing indexes for " + collection_name + ":", existing_indexes);
        print("Desired indexes for " + collection_name + ":", desired_indexes.map(idx => idx.name || idx.key)); //Show the index key if name isn't defined

        // Create missing indexes
        for (let i = 0; i < desired_indexes.length; i++) {
            let index_config = desired_indexes[i];
            let index_name = index_config.name || Object.keys(index_config.key).join('_'); // Create name if doesn't exist

            if (!existing_indexes.includes(index_name)) {
                print("Creating index '" + index_name + "' on collection '" + collection_name + "'");
                try {
                    db.getCollection(collection_name).createIndex(index_config.key, index_config.options);
                } catch (e) {
                    print("Error creating index '" + index_name + "' on collection '" + collection_name + "': " + e);
                }
            } else {
                print("Index '" + index_name + "' already exists on collection '" + collection_name + "'");
            }
        }

        // Delete indexes that are not desired (excluding _id_)
        for (let i = 0; i < existing_indexes.length; i++) {
            let existing_index_name = existing_indexes[i];
            if (existing_index_name === "_id_") continue; // Never delete the _id_ index
            let desired_index_names = desired_indexes.map(idx => idx.name || Object.keys(idx.key).join('_'));

            if (!desired_index_names.includes(existing_index_name)) {
                print("Dropping index '" + existing_index_name + "' on collection '" + collection_name + "'");
                try {
                    db.getCollection(collection_name).dropIndex(existing_index_name);
                } catch (e) {
                    print("Error dropping index '" + existing_index_name + "' on collection '" + collection_name + "': " + e);
                }
            }
        }
    }
}


// --- Delete collections not in the desired list ---
for (let i = 0; i < existing_collections.length; i++) {
    const existing_collection_name = existing_collections[i];
    if (!collections_config.hasOwnProperty(existing_collection_name)) {
        print("Deleting Collection: " + existing_collection_name);
        try {
            db.getCollection(existing_collection_name).drop();
        } catch (e) {
            print("Error deleting collection " + existing_collection_name + ": " + e);
        }
    }
}