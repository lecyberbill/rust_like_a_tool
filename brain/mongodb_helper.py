# [WFGY] Zone: SAFE | λ: 0.15 | Action: MongoDB read/write helper using pymongo
import sys
import os
import json
import csv
from pymongo import MongoClient
from bson import ObjectId

def json_serializable(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def clean_document(doc):
    if doc is None:
        return None
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, dict):
            doc[k] = clean_document(v)
        elif isinstance(v, list):
            doc[k] = [clean_document(item) if isinstance(item, dict) else (str(item) if isinstance(item, ObjectId) else item) for item in v]
    return doc

def get_client(connection_string):
    return MongoClient(connection_string)

def mongodb_find(connection_string, db_name, collection_name, filter_str, projection_str, destination):
    client = get_client(connection_string)
    db = client[db_name]
    coll = db[collection_name]

    query_filter = {}
    if filter_str and filter_str.strip():
        try:
            query_filter = json.loads(filter_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid filter JSON: {e}")

    query_projection = None
    if projection_str and projection_str.strip():
        try:
            query_projection = json.loads(projection_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid projection JSON: {e}")

    cursor = coll.find(query_filter, query_projection)
    results = []
    for doc in cursor:
        results.append(clean_document(doc))

    # Ensure parent dir exists
    dest_dir = os.path.dirname(destination)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    with open(destination, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=json_serializable)

    print(f"SUCCESS: Found {len(results)} documents from '{db_name}.{collection_name}' -> '{destination}'")

def mongodb_insert(connection_string, db_name, collection_name, source, mode):
    if not os.path.exists(source):
        print(f"Error: Source file '{source}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Load data
    _, ext = os.path.splitext(source.lower())
    docs = []
    if ext == ".json":
        with open(source, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            docs = data
        elif isinstance(data, dict):
            docs = [data]
    else:
        # CSV
        with open(source, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # convert type representation if necessary, but keep it simple as string values first
                docs.append(dict(row))

    if not docs:
        print("WARNING: No documents to insert.")
        return

    client = get_client(connection_string)
    db = client[db_name]
    coll = db[collection_name]

    if mode.lower() == "replace":
        print(f"[MONGO] Clearing collection '{collection_name}' (replace mode)...")
        coll.delete_many({})

    res = coll.insert_many(docs)
    print(f"SUCCESS: Inserted {len(res.inserted_ids)} documents into '{db_name}.{collection_name}' from '{source}'")

def main():
    if len(sys.argv) < 7:
        print("Usage: python mongodb_helper.py <find|insert> <connection_string> <database> <collection> <filter_json|source_path> <projection_json|mode>", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    connection_string = sys.argv[2]
    db_name = sys.argv[3]
    collection_name = sys.argv[4]

    try:
        if action == "find":
            filter_str = sys.argv[5]
            projection_str = sys.argv[6]
            if len(sys.argv) < 8:
                print("Error: Destination path missing for find action.", file=sys.stderr)
                sys.exit(1)
            destination = sys.argv[7]
            mongodb_find(connection_string, db_name, collection_name, filter_str, projection_str, destination)
        elif action == "insert":
            source = sys.argv[5]
            mode = sys.argv[6]
            mongodb_insert(connection_string, db_name, collection_name, source, mode)
        else:
            print(f"Error: Unknown action '{action}'", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        print(f"MongoDB Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
