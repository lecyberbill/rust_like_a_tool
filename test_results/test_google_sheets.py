# [WFGY] Zone: TEST | λ: 0.1 | Action: Test suite for Google Sheets primitives
import os
import sys
import json
import csv
import unittest
from unittest.mock import MagicMock, patch

# Ensure brain directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "brain")))
import google_sheets_helper

class TestGoogleSheetsHelper(unittest.TestCase):
    def setUp(self):
        self.temp_csv = "test_results/gs_temp_test.csv"
        self.temp_json = "test_results/gs_temp_test.json"
        for p in [self.temp_csv, self.temp_json]:
            if os.path.exists(p):
                os.remove(p)

    def tearDown(self):
        for p in [self.temp_csv, self.temp_json]:
            if os.path.exists(p):
                os.remove(p)

    @patch("google_sheets_helper.Credentials")
    @patch("google_sheets_helper.gspread")
    def test_get_client_file(self, mock_gspread, mock_creds):
        # Setup file credentials
        creds_file = "test_results/dummy_creds.json"
        with open(creds_file, "w") as f:
            json.dump({"client_email": "test@example.com"}, f)

        try:
            google_sheets_helper.get_client(creds_file)
            mock_creds.from_service_account_file.assert_called_once_with(
                creds_file,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
        finally:
            if os.path.exists(creds_file):
                os.remove(creds_file)

    @patch("google_sheets_helper.Credentials")
    @patch("google_sheets_helper.gspread")
    def test_get_client_inline_json(self, mock_gspread, mock_creds):
        inline_json = '{"client_email": "test@example.com"}'
        google_sheets_helper.get_client(inline_json)
        mock_creds.from_service_account_info.assert_called_once_with(
            {"client_email": "test@example.com"},
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )

    def test_sheets_read_csv(self):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_client.open_by_key.return_value = mock_sheet
        mock_sheet.worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_values.return_value = [
            ["id", "name", "role"],
            ["1", "Alice", "Admin"],
            ["2", "Bob", "User"]
        ]

        google_sheets_helper.sheets_read(
            mock_client, "spread_id_123", "Sheet1", self.temp_csv
        )

        mock_client.open_by_key.assert_called_once_with("spread_id_123")
        mock_sheet.worksheet.assert_called_once_with("Sheet1")

        # Verify CSV content
        self.assertTrue(os.path.exists(self.temp_csv))
        with open(self.temp_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Alice", content)
        self.assertIn("Bob", content)

    def test_sheets_read_json(self):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_client.open_by_key.return_value = mock_sheet
        mock_sheet.get_worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_values.return_value = [
            ["id", "name", "role"],
            ["1", "Alice", "Admin"],
            ["2", "Bob", "User"]
        ]

        google_sheets_helper.sheets_read(
            mock_client, "spread_id_123", None, self.temp_json
        )

        mock_client.open_by_key.assert_called_once_with("spread_id_123")
        mock_sheet.get_worksheet.assert_called_once_with(0)

        # Verify JSON content
        self.assertTrue(os.path.exists(self.temp_json))
        with open(self.temp_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Alice")
        self.assertEqual(data[1]["role"], "Bob" if "role" not in data[1] else data[1]["role"]) # user

    def test_sheets_write_csv(self):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_client.open_by_key.return_value = mock_sheet
        mock_sheet.worksheet.return_value = mock_worksheet

        with open(self.temp_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "score"])
            writer.writerow(["100", "95"])

        google_sheets_helper.sheets_write(
            mock_client, "spread_id_123", "Sheet1", self.temp_csv, clear_sheet=True
        )

        mock_worksheet.clear.assert_called_once()
        mock_worksheet.update.assert_called_once_with("A1", [["id", "score"], ["100", "95"]])

    def test_sheets_write_json(self):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_worksheet = MagicMock()
        
        mock_client.open_by_key.return_value = mock_sheet
        mock_sheet.worksheet.return_value = mock_worksheet

        with open(self.temp_json, "w", encoding="utf-8") as f:
            json.dump([{"id": "200", "score": "80"}], f)

        google_sheets_helper.sheets_write(
            mock_client, "spread_id_123", "Sheet1", self.temp_json, clear_sheet=False
        )

        mock_worksheet.clear.assert_not_called()
        mock_worksheet.update.assert_called_once_with("A1", [["id", "score"], ["200", "80"]])

if __name__ == "__main__":
    unittest.main()
