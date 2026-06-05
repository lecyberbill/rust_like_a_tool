# [WFGY] Zone: SAFE | λ: 0.1 | Action: Excel and XML exporter helper script
import sys
import os
import csv
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

def load_data(source_path):
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file '{source_path}' does not exist.")
    
    # Check extension
    _, ext = os.path.splitext(source_path.lower())
    if ext == '.json':
        with open(source_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure it is a list
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("JSON source must be an object or an array of objects.")
    else:
        # Default to CSV
        rows = []
        with open(source_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows

def to_xlsx(source_path, dest_path, sheet_name):
    # Import openpyxl dynamically
    import openpyxl
    
    data = load_data(source_path)
    if not data:
        print("WARNING: Source data is empty. Creating empty workbook.", file=sys.stderr)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        wb.save(dest_path)
        return
        
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    # Get headers from first object keys
    headers = list(data[0].keys())
    ws.append(headers)
    
    for row_idx, item in enumerate(data, start=2):
        row_values = [item.get(h, "") for h in headers]
        # Try to cast values to numbers to make it cleaner in Excel
        cleaned_values = []
        for val in row_values:
            if val is None:
                cleaned_values.append("")
            elif isinstance(val, (int, float)):
                cleaned_values.append(val)
            else:
                val_str = str(val)
                # Attempt conversion for strings that look like numeric
                try:
                    if '.' in val_str:
                        cleaned_values.append(float(val_str))
                    else:
                        cleaned_values.append(int(val_str))
                except ValueError:
                    cleaned_values.append(val_str)
        ws.append(cleaned_values)
        
    wb.save(dest_path)
    print(f"SUCCESS: Exported '{source_path}' to Excel '{dest_path}' (sheet: '{sheet_name}')")

def json_to_xml(source_path, dest_path, root_name, row_name):
    data = load_data(source_path)
    
    root = ET.Element(root_name)
    for idx, item in enumerate(data):
        row_el = ET.SubElement(root, row_name)
        for key, val in item.items():
            # Clean tag name (XML tags can't start with numbers or contain spaces easily)
            clean_key = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in key)
            if not clean_key or clean_key[0].isdigit():
                clean_key = f"col_{clean_key}"
                
            child = ET.SubElement(row_el, clean_key)
            if val is None:
                child.text = ""
            else:
                child.text = str(val)
                
    # Format with minidom for pretty printing
    xml_str = ET.tostring(root, encoding='utf-8')
    reparsed = minidom.parseString(xml_str)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Create parent dirs if necessary
    dest_dir = os.path.dirname(dest_path)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
        
    print(f"SUCCESS: Exported '{source_path}' to XML '{dest_path}' (root: '{root_name}', row: '{row_name}')")

def main():
    if len(sys.argv) < 4:
        print("Usage: python format_helper.py <xlsx|xml> <source> <destination> [args...]", file=sys.stderr)
        sys.exit(1)
        
    mode = sys.argv[1]
    source = sys.argv[2]
    destination = sys.argv[3]
    
    try:
        if mode == 'xlsx':
            sheet_name = sys.argv[4] if len(sys.argv) > 4 else "Sheet1"
            to_xlsx(source, destination, sheet_name)
        elif mode == 'xml':
            root_name = sys.argv[4] if len(sys.argv) > 4 else "root"
            row_name = sys.argv[5] if len(sys.argv) > 5 else "row"
            json_to_xml(source, destination, root_name, row_name)
        else:
            print(f"Error: Unknown mode '{mode}'", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error executing format_helper: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
