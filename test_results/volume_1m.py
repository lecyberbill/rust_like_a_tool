"""Test volumetrie 1M lignes avec calculs."""
import subprocess, json, time, sys

BIN = "rust_muscle/target/debug/rust_muscle.exe"
OUT = "workspace/output"

print("[1] Generation de 1 000 000 profils...")
t0 = time.perf_counter()
r = subprocess.run([BIN, "data.generate_fake",
    "--columns", "id:id,first_name:first_name,last_name:last_name,email:email,age:integer,active:boolean,salary:float",
    "--count", "1000000", "--destination", f"{OUT}/_vol_1m.csv", "--format", "csv"],
    capture_output=True, text=True, timeout=300)
assert r.returncode == 0, r.stderr[:200]
t1 = time.perf_counter()
print(f"  OK: {t1-t0:.1f}s")

print("[2] Clean + derive (calcul sur ID, age, salary)...")
r = subprocess.run([BIN, "data.clean",
    "--source", f"{OUT}/_vol_1m.csv",
    "--destination", f"{OUT}/_vol_1m_clean.csv",
    "--select-columns", "id,first_name,email,age,salary,tax",
    "--derive-columns", "tax=IF salary >= 50000 THEN salary * 0.3 ELSE salary * 0.15"],
    capture_output=True, text=True, timeout=300)
assert r.returncode == 0, r.stderr[:200]
t2 = time.perf_counter()
print(f"  OK: {t2-t1:.1f}s")

print("[3] Filtre + Metrique (moyenne)...")
r = subprocess.run([BIN, "data.filter",
    "--source", f"{OUT}/_vol_1m_clean.csv",
    "--destination", f"{OUT}/_vol_1m_filtered.csv",
    "--column-name", "age", "--operator", "greater_than",
    "--value", "18", "--has-headers", "true"],
    capture_output=True, text=True, timeout=300)
assert r.returncode == 0, r.stderr[:200]
t3 = time.perf_counter()
print(f"  Filtre OK: {t3-t2:.1f}s")

r = subprocess.run([BIN, "data.metrics",
    "--source", f"{OUT}/_vol_1m_filtered.csv",
    "--column-name", "salary", "--operation", "mean"],
    capture_output=True, text=True, timeout=300)
assert r.returncode == 0, r.stderr[:200]
result = json.loads(r.stdout.strip())
t4 = time.perf_counter()
print(f"  Metrique OK: {t4-t3:.1f}s")

total = t4 - t0
print(f"\n=== VOLUMETRIE 1M LIGNES ===")
print(f"Generation:  {t1-t0:.1f}s")
print(f"Clean+Calc:  {t2-t1:.1f}s")
print(f"Filtre:      {t3-t2:.1f}s")
print(f"Metrique:    {t4-t3:.1f}s")
print(f"Total:       {total:.1f}s")
print(f"Debit:       {1000000/total:.0f} lignes/s")
print(f"Salaire moyen: {result.get('value', 'N/A')}")
