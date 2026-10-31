"""Pharmacy prescription and stock tracker.

Records medicine stock and expiry dates, looks up patients and their
allergies in a small database, dispenses prescriptions and exports them
to a JSON file.
"""
import json
import sqlite3
from datetime import datetime


def setup_database():
    """Create an in-memory patients database and return the connection."""
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE patients (id TEXT, name TEXT, allergy TEXT)")
    cur.executemany(
        "INSERT INTO patients VALUES (?, ?, ?)",
        [
            ("P1", "Kavya", "penicillin"),
            ("P2", "Arjun", "none"),
            ("P3", "Meena", "ibuprofen"),
        ],
    )
    conn.commit()
    return conn


def find_patient(conn, name):
    """Return (id, allergy) rows for the given patient name."""
    cur = conn.cursor()
    query = "SELECT id, allergy FROM patients WHERE name = ?"
    return cur.execute(query, (name,)).fetchall()


def add_stock(stock, drug, units, expiry, batch_log=None):
    """Add units of a drug to stock and record the batch.

    Returns the number of batches in the log.
    """
    if batch_log is None:
        batch_log = []
    if units <= 0:
        raise ValueError(f"Units must be positive, got {units} for {drug}")
    current = stock.get(drug, {}).get("units", 0)
    stock[drug] = {"units": current + units, "expiry": expiry}
    batch_log.append((drug, units))
    return len(batch_log)


def dispense(conn, stock, prescriptions, patient_name, drug, units):
    """Dispense a drug to a patient. Return True on success."""
    patients = find_patient(conn, patient_name)
    if not patients:
        print("Unknown patient:", patient_name)
        return False
    patient_id, allergy = patients[0]
    if allergy.lower() != "none" and allergy.lower() == drug.lower():
        print("Allergy warning for", patient_name)
        return False
    if drug not in stock or stock[drug]["units"] < units:
        print("Insufficient stock of", drug)
        return False
    stock[drug]["units"] -= units
    prescriptions.append({
        "patient": patient_id,
        "drug": drug,
        "units": units,
        "time": str(datetime.now()),
    })
    return True


def expiring_soon(stock, days=30):
    """Return drugs that expire within the given number of days."""
    soon = []
    for drug, info in stock.items():
        exp = datetime.strptime(info["expiry"], "%Y-%m-%d")
        if (exp - datetime.now()).days < days:
            soon.append(drug)
    return soon


def export_prescriptions(prescriptions, file="prescriptions.json"):
    """Write the prescriptions list to a JSON file."""
    with open(file, "w", encoding="utf-8") as out:
        out.write(json.dumps(prescriptions))


def load_stock(file="stock.json"):
    """Load stock from a JSON file; return an empty dict if unavailable."""
    try:
        with open(file, encoding="utf-8") as src:
            return json.load(src)
    except (OSError, json.JSONDecodeError):
        return {}


def print_stock(stock):
    """Print every drug in stock with its units and expiry date."""
    print("Pharmacy Stock")
    for drug, info in stock.items():
        print(drug, "->", info["units"], "units, expires", info["expiry"])


def main():
    """Run the pharmacy demo."""
    conn = setup_database()
    stock = load_stock()
    prescriptions = []
    add_stock(stock, "Paracetamol", 100, "2027-03-01")
    add_stock(stock, "Amoxicillin", 20, "2025-12-31")
    add_stock(stock, "Penicillin", 50, "2027-01-15")
    add_stock(stock, "Ibuprofen", 15, "2026-11-30")
    print("Arjun gets Amoxicillin:",
          dispense(conn, stock, prescriptions, "Arjun", "Amoxicillin", 30))
    print("Kavya gets Penicillin:",
          dispense(conn, stock, prescriptions, "Kavya", "Penicillin", 10))
    print("Meena gets ibuprofen:",
          dispense(conn, stock, prescriptions, "Meena", "ibuprofen", 2))
    print("Unknown patient:",
          dispense(conn, stock, prescriptions, "Ghost", "Paracetamol", 5))
    name = input("Patient name to look up (Enter for Arjun): ") or "Arjun"
    print("Lookup result:", find_patient(conn, name))
    print("Expiring within 30 days:", expiring_soon(stock))
    export_prescriptions(prescriptions)
    print_stock(stock)


if __name__ == "__main__":
    main()
