"""Test volumetrie : 10K lignes, jointure, clean, filtre, metriques."""
import sys, os, json, time, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "brain"))
os.environ.setdefault("SECRET_VAULT_KEY", "test_vault_key")

BINARY = Path(__file__).parent.parent / "rust_muscle" / "target" / "debug" / "rust_muscle.exe"
OUTPUT = Path(__file__).parent.parent / "workspace" / "output"

# 1. Generer 10K utilisateurs
print("[1/5] Generation de 10 000 profils...")
t0 = time.perf_counter()
r = subprocess.run([str(BINARY), "data.generate_fake",
    "--columns", "id:id,first_name:first_name,last_name:last_name,email:email,age:integer,active:boolean,salary:float",
    "--count", "10000",
    "--destination", str(OUTPUT / "_vol_users.csv"),
    "--format", "csv"], capture_output=True, text=True, timeout=120)
assert r.returncode == 0, r.stderr
t1 = time.perf_counter()
print(f"  OK: {t1-t0:.1f}s")

# 2. Generer 1K commandes (jointure)
print("[2/5] Generation de 1 000 commandes...")
r = subprocess.run([str(BINARY), "data.generate_fake",
    "--columns", "order_id:id,user_id:id,product:pattern,amount:float,date:date",
    "--count", "1000",
    "--destination", str(OUTPUT / "_vol_orders.csv"),
    "--format", "csv"], capture_output=True, text=True, timeout=120)
assert r.returncode == 0, r.stderr
t2 = time.perf_counter()
print(f"  OK: {t2-t1:.1f}s")

# 3. Clean + derive colonnes (calcul)
print("[3/5] Clean + derive (calculs sur 10K lignes)...")
r = subprocess.run([str(BINARY), "data.clean",
    "--source", str(OUTPUT / "_vol_users.csv"),
    "--destination", str(OUTPUT / "_vol_cleaned.csv"),
    "--select-columns", "id,first_name,last_name,email,age,active,salary,tax",
    "--derive-columns", "tax=IF salary >= 50000 THEN salary * 0.3 ELSE salary * 0.15",
    "--fill-na", "age=0"],
    capture_output=True, text=True, timeout=120)
assert r.returncode == 0, r.stderr
t3 = time.perf_counter()
print(f"  OK: {t3-t2:.1f}s")

# 4. Filtre + metrique
print("[4/5] Filtre + moyenne...")
r = subprocess.run([str(BINARY), "data.filter",
    "--source", str(OUTPUT / "_vol_cleaned.csv"),
    "--destination", str(OUTPUT / "_vol_filtered.csv"),
    "--column-name", "active", "--operator", "equals",
    "--value", "True", "--has-headers", "true"],
    capture_output=True, text=True, timeout=120)
assert r.returncode == 0, r.stderr
t4 = time.perf_counter()
print(f"  OK: {t4-t3:.1f}s")

# 5. Metriques (moyenne)
print("[5/5] Metriques (moyenne salaire)...")
r = subprocess.run([str(BINARY), "data.metrics",
    "--source", str(OUTPUT / "_vol_filtered.csv"),
    "--column-name", "salary", "--operation", "mean"],
    capture_output=True, text=True, timeout=120)
assert r.returncode == 0, r.stderr
result = json.loads(r.stdout.strip())
t5 = time.perf_counter()
print(f"  OK: {t5-t4:.1f}s")

print(f"\n=== RESULTATS VOLUMETRIE ===")
print(f"Total: {t5-t0:.1f}s")
print(f"Generation: {t1-t0:.1f}s")
print(f"Commandes:  {t2-t1:.1f}s")
print(f"Clean+Calc: {t3-t2:.1f}s")
print(f"Filtre:     {t4-t3:.1f}s")
print(f"Metrique:   {t5-t4:.1f}s")
print(f"Actifs: {result.get('value', 'N/A')}")
print(f"Soit {10000/(t5-t0):.0f} lignes/seconde")
