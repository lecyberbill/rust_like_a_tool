# [WFGY] Zone: SAFE | λ: 0.2 | Action: Pure Python fake data generator helper (fake_gen_helper.py)
import os
import sys
import json
import csv
import random
import re
from datetime import datetime, timedelta

DEFAULT_GEN_DIR = 'D:/Projet/fake_GEN'
LISTS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'fake_gen_lists.json')

DEFAULT_FALLBACK_LISTS = {
    "firstNames": ["Jean", "Marie", "Pierre", "Sophie", "Lucas", "Julie", "Thomas", "Emma", "Nicolas", "Sarah"],
    "lastNames": ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau"],
    "domains": ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "orange.fr", "laposte.net"],
    "countries": [
        {"name": "France", "code": "FR", "postalFormat": "#####"},
        {"name": "Belgique", "code": "BE", "postalFormat": "####"},
        {"name": "Suisse", "code": "CH", "postalFormat": "####"},
        {"name": "Canada", "code": "CA", "postalFormat": "A#A #A#"}
    ],
    "cities": ["Paris", "Lyon", "Marseille", "Bruxelles", "Genève", "Montréal", "Lille", "Bordeaux", "Nantes", "Strasbourg"],
    "streets": ["Rue de la Paix", "Avenue des Champs-Élysées", "Rue de la Gare", "Boulevard Victor Hugo", "Rue Principale"],
    "loremWords": ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit", "sed", "do"],
    "phonePrefixes": ["06", "07", "01", "02", "03", "04", "05"]
}

def load_lists(gen_dir):
    """Loads list data from the static JSON file or falls back to default lists if missing."""
    if os.path.exists(LISTS_JSON_PATH):
        try:
            with open(LISTS_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[LOAD WARNING] Failed to load {LISTS_JSON_PATH}: {e}. Falling back to default list.", file=sys.stderr)
            
    return DEFAULT_FALLBACK_LISTS


# Moteur de génération Python
class FakeGenerator:
    def __init__(self, lists):
        self.lists = lists

    def generate_pattern(self, pattern):
        res = []
        for ch in pattern:
            if ch == '#':
                res.append(str(random.randint(0, 9)))
            elif ch == 'A':
                res.append(chr(random.randint(65, 90)))
            elif ch == 'a':
                res.append(chr(random.randint(97, 122)))
            elif ch == 'X':
                res.append(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))
            elif ch == 'x':
                res.append(random.choice("abcdefghijklmnopqrstuvwxyz0123456789"))
            elif ch == '?':
                res.append(chr(random.choice(list(range(65, 90)) + list(range(97, 122)))))
            else:
                res.append(ch)
        return "".join(res)

    def generate_value(self, col_type, col_config, row_index):
        if col_type == 'id':
            start = int(col_config.get('start', 1))
            step = int(col_config.get('step', 1))
            return str(start + row_index * step)
            
        elif col_type == 'boolean':
            return str(random.random() < 0.5).lower()
            
        elif col_type == 'integer':
            min_val = int(col_config.get('min', 0))
            max_val = int(col_config.get('max', 99999))
            return str(random.randint(min_val, max_val))
            
        elif col_type == 'float':
            min_val = float(col_config.get('min', 0.0))
            max_val = float(col_config.get('max', 99999.0))
            decimals = int(col_config.get('decimals', 2))
            return f"{random.uniform(min_val, max_val):.{decimals}f}"
            
        elif col_type == 'date':
            min_date_str = col_config.get('min', '2000-01-01')
            max_date_str = col_config.get('max', datetime.today().strftime('%Y-%m-%d'))
            fmt = col_config.get('format', 'YYYY-MM-DD')
            
            try:
                min_d = datetime.strptime(min_date_str, '%Y-%m-%d')
                max_d = datetime.strptime(max_date_str, '%Y-%m-%d')
            except Exception:
                min_d = datetime(2000, 1, 1)
                max_d = datetime.today()
                
            delta_days = (max_d - min_d).days
            rand_days = random.randint(0, max(0, delta_days))
            res_date = min_d + timedelta(days=rand_days)
            
            # Format replacement
            return fmt.replace('YYYY', str(res_date.year)).replace('MM', f"{res_date.month:02d}").replace('DD', f"{res_date.day:02d}")
            
        elif col_type == 'firstName':
            return random.choice(self.lists.get('firstNames', DEFAULT_FALLBACK_LISTS['firstNames']))
            
        elif col_type == 'lastName':
            return random.choice(self.lists.get('lastNames', DEFAULT_FALLBACK_LISTS['lastNames']))
            
        elif col_type == 'fullName':
            fn = self.generate_value('firstName', {}, row_index)
            ln = self.generate_value('lastName', {}, row_index)
            return f"{fn} {ln}"
            
        elif col_type == 'email':
            fn = self.generate_value('firstName', {}, row_index).lower()
            ln = self.generate_value('lastName', {}, row_index).lower()
            sep = random.choice(['.', '-', '_', ''])
            num = str(random.randint(1, 999)) if random.random() < 0.3 else ''
            dom = random.choice(self.lists.get('domains', DEFAULT_FALLBACK_LISTS['domains']))
            return f"{fn}{sep}{ln}{num}@{dom}"
            
        elif col_type == 'phone':
            prefix = col_config.get('prefix', random.choice(self.lists.get('phonePrefixes', DEFAULT_FALLBACK_LISTS['phonePrefixes'])))
            digits = "".join(str(random.randint(0, 9)) for _ in range(8))
            return f"{prefix}{digits}"
            
        elif col_type == 'country':
            country_obj = random.choice(self.lists.get('countries', DEFAULT_FALLBACK_LISTS['countries']))
            if col_config.get('format') == 'code':
                return country_obj.get('code', 'FR')
            return country_obj.get('name', 'France')
            
        elif col_type == 'city':
            return random.choice(self.lists.get('cities', DEFAULT_FALLBACK_LISTS['cities']))
            
        elif col_type == 'address':
            num = random.randint(1, 999)
            street = random.choice(self.lists.get('streets', DEFAULT_FALLBACK_LISTS['streets']))
            city = self.generate_value('city', {}, row_index)
            return f"{num}, {street}, {city}"
            
        elif col_type == 'postalCode':
            c_name = col_config.get('country')
            country_obj = None
            if c_name:
                for c in self.lists.get('countries', []):
                    if c.get('name') == c_name or c.get('code') == c_name:
                        country_obj = c
                        break
            if not country_obj:
                country_obj = random.choice(self.lists.get('countries', DEFAULT_FALLBACK_LISTS['countries']))
            fmt = country_obj.get('postalFormat', '#####')
            return self.generate_pattern(fmt)
            
        elif col_type == 'text':
            min_w = int(col_config.get('minWords', 5))
            max_w = int(col_config.get('maxWords', 20))
            words_pool = self.lists.get('loremWords', DEFAULT_FALLBACK_LISTS['loremWords'])
            cnt = random.randint(min_w, max_w)
            words = [random.choice(words_pool) for _ in range(cnt)]
            if words:
                words[0] = words[0].capitalize()
            return " ".join(words) + "."
            
        elif col_type == 'pattern':
            pat = col_config.get('pattern', '#####')
            return self.generate_pattern(pat)
            
        return ''

def parse_columns_string(cols_str):
    """Parses simple cols string 'col:type,col2:type2' or a full JSON string."""
    cols_str = cols_str.strip()
    if cols_str.startswith('[') or cols_str.startswith('{'):
        try:
            return json.loads(cols_str)
        except Exception as e:
            print(f"[ERROR] Failed to parse columns JSON: {e}", file=sys.stderr)
            sys.exit(1)
            
    # Simple syntax parser
    columns = []
    for part in cols_str.split(','):
        if not part.strip():
            continue
        subparts = part.strip().split(':')
        name = subparts[0].strip()
        col_type = subparts[1].strip() if len(subparts) > 1 else 'text'
        columns.append({
            "name": name,
            "type": col_type,
            "config": {}
        })
    return columns

def main():
    if len(sys.argv) < 5:
        print("Usage: python fake_gen_helper.py <generator_path> <columns> <count> <destination> [format]", file=sys.stderr)
        sys.exit(1)
        
    gen_dir = sys.argv[1] or DEFAULT_GEN_DIR
    columns_str = sys.argv[2]
    count = int(sys.argv[3])
    destination = sys.argv[4]
    export_format = sys.argv[5].lower() if len(sys.argv) > 5 else 'csv'
    
    # Load lists
    lists = load_lists(gen_dir)
    generator = FakeGenerator(lists)
    
    columns = parse_columns_string(columns_str)
    
    # Generate rows
    rows = []
    for i in range(count):
        row = {}
        for col in columns:
            name = col["name"]
            c_type = col["type"]
            c_cfg = col.get("config", {})
            row[name] = generator.generate_value(c_type, c_cfg, i)
        rows.append(row)
        
    # Write to destination
    dest_dir = os.path.dirname(destination)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        
    if export_format == 'json':
        with open(destination, 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
    else:
        # CSV format
        if not rows:
            return
        headers = list(rows[0].keys())
        with open(destination, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
                
    print(f"SUCCESS: Generated {count} fake rows in '{destination}' (format: {export_format})")

if __name__ == '__main__':
    main()
