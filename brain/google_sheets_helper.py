# [WFGY] Zone: SAFE | λ: 0.15 | Action: Google Sheets read/write helper using gspread
import sys
import os
import json
import csv
import gspread
from google.oauth2.service_account import Credentials

def get_client(credentials_json_or_path):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Check if the credentials string is a path or inline JSON
    if os.path.exists(credentials_json_or_path):
        creds = Credentials.from_service_account_file(credentials_json_or_path, scopes=scopes)
    else:
        try:
            info = json.loads(credentials_json_or_path)
            creds = Credentials.from_service_account_info(info, scopes=scopes)
        except json.JSONDecodeError as e:
            raise ValueError(f"Credentials parameter must be a valid file path or valid JSON string. Error: {e}")
    return gspread.authorize(creds)

def sheets_read(client, spreadsheet_id, worksheet_title, local_path):
    sheet = client.open_by_key(spreadsheet_id)
    if worksheet_title:
        worksheet = sheet.worksheet(worksheet_title)
    else:
        worksheet = sheet.get_worksheet(0)
    
    # Get all values as list of lists
    all_values = worksheet.get_all_values()
    
    # Ensure parent dir exists
    local_dir = os.path.dirname(local_path)
    if local_dir and not os.path.exists(local_dir):
        os.makedirs(local_dir, exist_ok=True)
        
    _, ext = os.path.splitext(local_path.lower())
    if ext == ".json":
        if not all_values:
            data = []
        else:
            headers = all_values[0]
            data = []
            for row in all_values[1:]:
                # Fill missing columns with empty string
                row_dict = {}
                for idx, h in enumerate(headers):
                    row_dict[h] = row[idx] if idx < len(row) else ""
                data.append(row_dict)
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        # Default to CSV
        with open(local_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(all_values)
            
    print(f"SUCCESS: Read Google Sheet '{spreadsheet_id}' -> '{local_path}'")

def sheets_write(client, spreadsheet_id, worksheet_title, local_path, clear_sheet):
    if not os.path.exists(local_path):
        print(f"Error: Local file '{local_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    # Read local data
    _, ext = os.path.splitext(local_path.lower())
    rows = []
    if ext == ".json":
        with open(local_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            headers = list(data[0].keys())
            rows.append(headers)
            for item in data:
                rows.append([str(item.get(h, "")) for h in headers])
    else:
        with open(local_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

    sheet = client.open_by_key(spreadsheet_id)
    if worksheet_title:
        try:
            worksheet = sheet.worksheet(worksheet_title)
        except gspread.exceptions.WorksheetNotFound:
            # Create if it doesn't exist
            worksheet = sheet.add_worksheet(title=worksheet_title, rows="100", cols="20")
    else:
        worksheet = sheet.get_worksheet(0)

    if clear_sheet:
        worksheet.clear()

    if rows:
        worksheet.update("A1", rows)
        
    print(f"SUCCESS: Wrote local file '{local_path}' -> Google Sheet '{spreadsheet_id}' (worksheet: '{worksheet.title}')")

def main():
    if len(sys.argv) < 7:
        print("Usage: python google_sheets_helper.py <read|write> <credentials_json_or_path> <spreadsheet_id> <worksheet_title> <local_path> [clear_sheet (true/false)]", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    credentials = sys.argv[2]
    spreadsheet_id = sys.argv[3]
    worksheet_title = sys.argv[4]
    local_path = sys.argv[5]
    clear_sheet = sys.argv[6].lower() == "true" if len(sys.argv) > 6 else True

    try:
        client = get_client(credentials)
        if action == "read":
            sheets_read(client, spreadsheet_id, worksheet_title, local_path)
        elif action == "write":
            sheets_write(client, spreadsheet_id, worksheet_title, local_path, clear_sheet)
        else:
            print(f"Error: Unknown action '{action}'", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        print(f"Google Sheets Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
