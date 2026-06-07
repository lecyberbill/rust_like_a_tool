# [WFGY] Zone: TEST | λ: 0.1 | Action: Test suite for MongoDB primitives
import os
import sys
import json
import csv
import unittest
from unittest.mock import MagicMock, patch
from bson import ObjectId

# Ensure brain directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "brain")))
import mongodb_helper

class TestMongoDBHelper(unittest.TestCase):
    def setUp(self):
        self.temp_dest = "test_results/mongo_temp_out.json"
        self.temp_src_json = "test_results/mongo_temp_src.json"
        self.temp_src_csv = "test_results/mongo_temp_src.csv"
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        for p in [self.temp_dest, self.temp_src_json, self.temp_src_csv]:
            if os.path.exists(p):
                os.remove(p)

    @patch("mongodb_helper.MongoClient")
    def test_mongodb_find(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_coll = MagicMock()
        mock_db.__getitem__.return_value = mock_coll

        # Simulate finding two docs, one containing an ObjectId
        oid = ObjectId()
        mock_coll.find.return_value = [
            {"_id": oid, "name": "Jean", "age": 30},
            {"_id": ObjectId(), "name": "Marie", "age": 25}
        ]

        mongodb_helper.mongodb_find(
            connection_string="mongodb://mock:27017",
            db_name="test_db",
            collection_name="users",
            filter_str='{"age": {"$gt": 20}}',
            projection_str='{"name": 1, "age": 1}',
            destination=self.temp_dest
        )

        mock_client_class.assert_called_once_with("mongodb://mock:27017")
        mock_client.__getitem__.assert_called_once_with("test_db")
        mock_db.__getitem__.assert_called_once_with("users")
        mock_coll.find.assert_called_once_with({"age": {"$gt": 20}}, {"name": 1, "age": 1})

        # Verify output file
        self.assertTrue(os.path.exists(self.temp_dest))
        with open(self.temp_dest, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["_id"], str(oid))
        self.assertEqual(data[0]["name"], "Jean")

    @patch("mongodb_helper.MongoClient")
    def test_mongodb_insert_json(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_coll = MagicMock()
        mock_db.__getitem__.return_value = mock_coll

        # Seed JSON source
        src_data = [{"name": "Sophie", "score": 98}]
        with open(self.temp_src_json, "w", encoding="utf-8") as f:
            json.dump(src_data, f)

        mock_coll.insert_many.return_value.inserted_ids = [ObjectId()]

        mongodb_helper.mongodb_insert(
            connection_string="mongodb://mock:27017",
            db_name="test_db",
            collection_name="users",
            source=self.temp_src_json,
            mode="insert"
        )

        mock_coll.delete_many.assert_not_called()
        mock_coll.insert_many.assert_called_once_with(src_data)

    @patch("mongodb_helper.MongoClient")
    def test_mongodb_insert_csv(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_coll = MagicMock()
        mock_db.__getitem__.return_value = mock_coll

        # Seed CSV source
        with open(self.temp_src_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "score"])
            writer.writeheader()
            writer.writerow({"name": "Lucas", "score": "87"})

        mock_coll.insert_many.return_value.inserted_ids = [ObjectId()]

        mongodb_helper.mongodb_insert(
            connection_string="mongodb://mock:27017",
            db_name="test_db",
            collection_name="users",
            source=self.temp_src_csv,
            mode="replace"
        )

        mock_coll.delete_many.assert_called_once_with({})
        mock_coll.insert_many.assert_called_once_with([{"name": "Lucas", "score": "87"}])

if __name__ == "__main__":
    unittest.main()
