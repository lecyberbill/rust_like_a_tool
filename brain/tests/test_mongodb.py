"""Tests MongoDB primitives (mockés, sans serveur)"""
import os, json, csv
from unittest.mock import MagicMock, patch
from bson import ObjectId

import mongodb_helper


class TestMongoDBFind:
    def setup_method(self):
        self.dest = "/tmp/_mongo_test_out.json"

    def teardown_method(self):
        for p in [self.dest]:
            if os.path.exists(p):
                os.remove(p)

    @patch("mongodb_helper.MongoClient")
    def test_find_with_filter(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_db = MagicMock()
        mock_coll = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_coll

        oid = ObjectId()
        mock_coll.find.return_value = [
            {"_id": oid, "name": "Jean", "age": 30},
            {"_id": ObjectId(), "name": "Marie", "age": 25},
        ]

        mongodb_helper.mongodb_find(
            connection_string="mongodb://mock:27017",
            db_name="test_db",
            collection_name="users",
            filter_str='{"age": {"$gt": 20}}',
            projection_str='{"name": 1, "age": 1}',
            destination=self.dest,
        )

        assert os.path.exists(self.dest)
        with open(self.dest, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["_id"] == str(oid)
        assert data[0]["name"] == "Jean"

    @patch("mongodb_helper.MongoClient")
    def test_find_empty_filter(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_coll = MagicMock()
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_coll
        mock_coll.find.return_value = []

        mongodb_helper.mongodb_find(
            connection_string="mongodb://mock:27017",
            db_name="db",
            collection_name="coll",
            filter_str="",
            projection_str="",
            destination=self.dest,
        )

        assert os.path.exists(self.dest)
        with open(self.dest, encoding="utf-8") as f:
            data = json.load(f)
        assert data == []


class TestMongoDBInsert:
    def setup_method(self):
        self.src = "/tmp/_mongo_src.json"

    def teardown_method(self):
        for p in [self.src]:
            if os.path.exists(p):
                os.remove(p)

    @patch("mongodb_helper.MongoClient")
    def test_insert_json_append(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_coll = MagicMock()
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_coll

        data = [{"name": "Sophie", "score": 98}]
        with open(self.src, "w", encoding="utf-8") as f:
            json.dump(data, f)

        mongodb_helper.mongodb_insert(
            connection_string="mongodb://mock:27017",
            db_name="db",
            collection_name="coll",
            source=self.src,
            mode="insert",
        )

        mock_coll.delete_many.assert_not_called()
        mock_coll.insert_many.assert_called_once_with(data)

    @patch("mongodb_helper.MongoClient")
    def test_insert_csv_replace(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_coll = MagicMock()
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_coll

        csv_path = self.src.replace(".json", ".csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["name", "score"])
            w.writerow(["Lucas", "87"])

        mongodb_helper.mongodb_insert(
            connection_string="mongodb://mock:27017",
            db_name="db",
            collection_name="coll",
            source=csv_path,
            mode="replace",
        )

        mock_coll.delete_many.assert_called_once_with({})
        mock_coll.insert_many.assert_called_once_with([{"name": "Lucas", "score": "87"}])
        os.remove(csv_path)
