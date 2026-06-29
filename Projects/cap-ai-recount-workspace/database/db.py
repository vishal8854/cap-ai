import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "cap_ai.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS recount_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE NOT NULL,
            branch TEXT NOT NULL,
            cashier TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'Open',
            observer TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS observer_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observer_name TEXT NOT NULL,
            branch TEXT NOT NULL,
            schedule_date TEXT NOT NULL,
            shift TEXT NOT NULL,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tally_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT,
            doc_type TEXT NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            txn_date TEXT,
            from_account TEXT,
            to_account TEXT,
            amount REAL,
            approved_by TEXT,
            risk_score REAL,
            pattern TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS interest_validation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT NOT NULL,
            principal REAL NOT NULL,
            rate REAL NOT NULL,
            time_days REAL DEFAULT 365,
            actual_interest REAL NOT NULL,
            expected_interest REAL,
            variance_pct REAL,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS idle_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT NOT NULL,
            balance REAL NOT NULL,
            last_transaction_date TEXT,
            idle_days INTEGER,
            recommendation TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS signatory_verification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT NOT NULL,
            authorized_signatory TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            action TEXT NOT NULL,
            module TEXT,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            table_name TEXT,
            record_id TEXT,
            action TEXT,
            old_value TEXT,
            new_value TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cur.execute("SELECT COUNT(*) FROM recount_cases")
    if cur.fetchone()[0] == 0:
        _seed_sample_data(cur)

    conn.commit()
    conn.close()


def _seed_sample_data(cur: sqlite3.Cursor) -> None:
    cases = [
        ("RC-2026-001", "Mumbai Central", "Rajesh Kumar", 2450000, "In Progress", "Priya Sharma"),
        ("RC-2026-002", "Delhi North", "Amit Patel", 1875000, "Open", None),
        ("RC-2026-003", "Bangalore IT", "Sneha Reddy", 3200000, "Scheduled", "Vikram Singh"),
        ("RC-2026-004", "Chennai South", "Karthik Iyer", 980000, "Closed", "Anita Desai"),
        ("RC-2026-005", "Hyderabad West", "Farhan Ali", 1560000, "In Progress", "Meera Nair"),
    ]
    cur.executemany(
        "INSERT INTO recount_cases (case_id, branch, cashier, amount, status, observer) VALUES (?,?,?,?,?,?)",
        cases,
    )

    schedules = [
        ("Priya Sharma", "Mumbai Central", "2026-06-26", "Morning", "Recount observation"),
        ("Vikram Singh", "Bangalore IT", "2026-06-27", "Afternoon", "Cash tally verification"),
        ("Anita Desai", "Chennai South", "2026-06-25", "Morning", "Completed"),
    ]
    cur.executemany(
        "INSERT INTO observer_schedule (observer_name, branch, schedule_date, shift, remarks) VALUES (?,?,?,?,?)",
        schedules,
    )

    txns = [
        ("TXN-1001", "2026-05-01", "ACC-001", "ACC-002", 500000, "John Smith"),
        ("TXN-1002", "2026-05-02", "ACC-002", "ACC-003", 500000, "Jane Doe"),
        ("TXN-1003", "2026-05-03", "ACC-003", "ACC-001", 500000, "Unknown User"),
        ("TXN-1004", "2026-05-05", "ACC-004", "ACC-005", 250000, "John Smith"),
        ("TXN-1005", "2026-05-06", "ACC-005", "ACC-004", 250000, "John Smith"),
        ("TXN-1006", "2026-05-10", "ACC-006", "ACC-007", 100000, "Jane Doe"),
        ("TXN-1007", "2026-05-15", "ACC-001", "ACC-008", 75000, "External Approver"),
    ]
    cur.executemany(
        "INSERT INTO transactions (transaction_id, txn_date, from_account, to_account, amount, approved_by) VALUES (?,?,?,?,?,?)",
        txns,
    )

    interest = [
        ("ACC-101", 1000000, 0.065, 365, 72000),
        ("ACC-102", 2500000, 0.055, 365, 160000),
        ("ACC-103", 500000, 0.07, 365, 42000),
    ]
    for row in interest:
        expected = row[1] * row[2] * (row[3] / 365)
        variance = ((row[4] - expected) / expected * 100) if expected else 0
        status = "Overcharge" if variance > 1 else "Undercharge" if variance < -1 else "OK"
        cur.execute(
            """INSERT INTO interest_validation
               (account, principal, rate, time_days, actual_interest, expected_interest, variance_pct, status)
               VALUES (?,?,?,?,?,?,?,?)""",
            (row[0], row[1], row[2], row[3], row[4], expected, variance, status),
        )

    idle = [
        ("ACC-201", 850000, "2026-02-15", 130, "Sweep Account"),
        ("ACC-202", 1200000, "2026-01-20", 156, "Invest in FD"),
        ("ACC-203", 450000, "2026-04-01", 85, "Review Account"),
    ]
    cur.executemany(
        "INSERT INTO idle_accounts (account, balance, last_transaction_date, idle_days, recommendation) VALUES (?,?,?,?,?)",
        idle,
    )

    signatories = [
        ("ACC-001", "John Smith"),
        ("ACC-002", "Jane Doe"),
        ("ACC-003", "John Smith"),
        ("ACC-004", "John Smith"),
        ("ACC-005", "Jane Doe"),
    ]
    cur.executemany(
        "INSERT INTO signatory_verification (account, authorized_signatory) VALUES (?,?)",
        signatories,
    )
