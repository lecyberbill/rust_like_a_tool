# [WFGY] Zone: SAFE | λ: 0.2 | Action: Create data anonymization integration test

import asyncio
import json
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / "brain"))
from orchestrator import Orchestrator

async def test_anonymize():
    # Setup test directory
    test_dir = Path("test_results")
    test_dir.mkdir(exist_ok=True)

    # 1. Create source file with sensitive PII data
    source_file = test_dir / "pii_source.csv"
    with open(source_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "email", "phone", "salary"])
        writer.writerow(["1", "Jean Dupont", "jean.dupont@company.com", "+33612345678", "5000"])
        writer.writerow(["2", "Marie Martin", "marie.martin@gmail.com", "+33698765432", "6000"])
        writer.writerow(["3", "Pierre", "pierre@yahoo.fr", "0102030405", "4500"])

    # Output path for anonymized dataset
    dest_file = test_dir / "anonymized_output.csv"

    # Recipe specifying data.anonymize
    recipe = {
        "plan_id": "test_data_anonymization_flow",
        "intent_analysis": "Verification de data.anonymize avec les strategies mask, mask_email, hash et replace",
        "steps": [
            {
                "step": 1,
                "primitive": "data.anonymize",
                "ui": {
                    "label": "Anonymisation des donnees"
                },
                "args": {
                    "source": str(source_file.resolve()).replace("\\", "/"),
                    "destination": str(dest_file.resolve()).replace("\\", "/"),
                    "rules": "name:hash,email:mask_email,phone:mask,salary:replace"
                }
            }
        ]
    }

    orchestrator = Orchestrator()
    print("--- Lancement du test de la primitive data.anonymize ---")
    success = await orchestrator.run_recipe(recipe)

    if not success:
        print("\n[VERIFICATION] FAIL: L'orchestrateur a renvoye un echec d'execution.")
        return

    # Verify anonymized_output.csv content
    if not dest_file.exists():
        print("\n[VERIFICATION] FAIL: Le fichier de destination n'a pas ete cree.")
        return

    with open(dest_file, mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    print("\n--- Rows after anonymization: ---")
    for r in rows:
        print(r)

    # Assertions
    passed = True
    for r in rows:
        name = r.get("name")
        email = r.get("email")
        phone = r.get("phone")
        salary = r.get("salary")

        # 1. Salary must be [REDACTED]
        if salary != "[REDACTED]":
            print(f"[VERIFICATION] FAIL: Salary non remplace pour id {r['id']} (obtenu: {salary})")
            passed = False

        # 2. Email local part must be masked but domain kept
        if "@" in email:
            local, domain = email.split("@", 1)
            if "*" not in local or len(local) < 3:
                print(f"[VERIFICATION] FAIL: Email local part non masque pour id {r['id']} (obtenu: {email})")
                passed = False
        else:
            print(f"[VERIFICATION] FAIL: Email invalide ou non conserve pour id {r['id']} (obtenu: {email})")
            passed = False

        # 3. Name must be hashed as a 16-character hex string (FNV-1a 64-bit)
        if len(name) != 16 or not all(c in "0123456789abcdef" for c in name):
            print(f"[VERIFICATION] FAIL: Nom non hashed correctement pour id {r['id']} (obtenu: {name})")
            passed = False

        # 4. Phone must be masked
        if "*" not in phone:
            print(f"[VERIFICATION] FAIL: Telephone non masque pour id {r['id']} (obtenu: {phone})")
            passed = False

    if passed:
        print("\n[VERIFICATION] PASS: data.anonymize a applique toutes les strategies d'anonymisation correctement !")
    else:
        print("\n[VERIFICATION] FAIL: Les strategies d'anonymisation ne sont pas conformes.")

if __name__ == "__main__":
    asyncio.run(test_anonymize())
