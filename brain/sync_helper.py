"""data.sync — synchronisation bidirectionnelle entre fichier et base de donnees."""
import sys, json, csv, sqlite3

def sync_csv_to_db(csv_path, db_url, table_name, key_columns):
    conn = sqlite3.connect(db_url.replace("sqlite://", ""))
    cur = conn.cursor()
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return {"inserted": 0, "updated": 0, "deleted": 0}
    cols = list(rows[0].keys())
    keys = [k.strip() for k in key_columns.split(",")] if key_columns else [cols[0]]
    
    # Verifier si la table existe
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cur.fetchone():
        col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
        pk = ", ".join(f'"{k}"' for k in keys)
        cur.execute(f'CREATE TABLE "{table_name}" ({col_defs}, PRIMARY KEY ({pk}))')
    
    # Lire les cles existantes
    cur.execute(f'SELECT DISTINCT "{keys[0]}" FROM "{table_name}"')
    existing_keys = set(str(r[0]) for r in cur.fetchall())
    new_keys = set(str(r[keys[0]]) for r in rows)
    
    to_insert = new_keys - existing_keys
    to_delete = existing_keys - new_keys
    to_update = new_keys & existing_keys
    
    for r in rows:
        if str(r[keys[0]]) in to_insert:
            placeholders = ", ".join("?" for _ in cols)
            col_names = ", ".join(f'"{c}"' for c in cols)
            vals = [r[c] for c in cols]
            cur.execute(f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})', vals)
        elif str(r[keys[0]]) in to_update:
            set_clause = ", ".join(f'"{c}"=?' for c in cols if c not in keys)
            where_clause = " AND ".join(f'"{k}"=?' for k in keys)
            vals = [r[c] for c in cols if c not in keys] + [r[k] for k in keys]
            cur.execute(f'UPDATE "{table_name}" SET {set_clause} WHERE {where_clause}', vals)
    
    for k in to_delete:
        cur.execute(f'DELETE FROM "{table_name}" WHERE "{keys[0]}"=?', (k,))
    
    conn.commit()
    conn.close()
    return {"inserted": len(to_insert), "updated": len(to_update), "deleted": len(to_delete)}

def main():
    if len(sys.argv) < 5:
        print("Usage: python sync_helper.py <csv_path> <db_url> <table_name> <key_columns>", file=sys.stderr)
        sys.exit(1)
    result = sync_csv_to_db(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print(json.dumps(result))

if __name__ == "__main__":
    main()
