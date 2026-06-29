"""SQLite database layer for CAP AI."""

import json
import sqlite3
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from config import DB_PATH, DATABASE_DIR, UPLOADS_DIR


def get_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _rows_to_df(rows: list) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS litigation_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE NOT NULL,
            case_name TEXT NOT NULL,
            election_type TEXT,
            state TEXT,
            district TEXT,
            court TEXT,
            petitioner TEXT,
            respondent TEXT,
            filing_date TEXT,
            hearing_date TEXT,
            current_status TEXT DEFAULT 'Open',
            priority TEXT DEFAULT 'Medium',
            advocate TEXT,
            documents TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            complainant_name TEXT NOT NULL,
            booth TEXT,
            constituency TEXT,
            category TEXT,
            description TEXT,
            evidence_path TEXT,
            assigned_officer TEXT,
            status TEXT DEFAULT 'Open',
            resolution TEXT,
            resolution_date TEXT,
            priority TEXT DEFAULT 'Medium',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS financial_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            txn_date TEXT,
            from_account TEXT,
            to_account TEXT,
            amount REAL,
            approved_by TEXT,
            risk_score REAL,
            risk_level TEXT,
            pattern TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS signatories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT NOT NULL,
            authorized_signatory TEXT NOT NULL,
            expiry_date TEXT,
            dual_approval_required INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Active',
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
            recovery_opportunity REAL,
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
            projected_earnings REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            file_type TEXT,
            module TEXT,
            uploaded_by TEXT,
            row_count INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            title TEXT NOT NULL,
            filepath TEXT,
            generated_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            action TEXT NOT NULL,
            module TEXT,
            details TEXT,
            ip_address TEXT,
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
            ip_address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cur.execute("SELECT COUNT(*) FROM litigation_cases")
    if cur.fetchone()[0] == 0:
        _seed_data(cur)

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        for login_id, info in [
            ("admin", "admin123", "Admin User", "Admin"),
            ("investigator", "inv123", "Investigator User", "Investigator"),
            ("compliance", "comp123", "Compliance Officer", "Compliance Officer"),
            ("legal", "legal123", "Legal Officer", "Legal Officer"),
            ("viewer", "view123", "Viewer User", "Viewer"),
        ]:
            cur.execute(
                "INSERT INTO users (username, password_hash, display_name, role) VALUES (?,?,?,?)",
                (login_id, login_id + "_hash", info[2], info[3]),
            )

    conn.commit()
    conn.close()


def _seed_data(cur: sqlite3.Cursor) -> None:
    cases = [
        ("EL-2026-001", "Election Petition - Mumbai North", "Parliamentary", "Maharashtra", "Mumbai North",
         "Bombay High Court", "Rajesh Kumar", "Election Commission", "2026-01-15", "2026-07-10",
         "Open", "High", "Adv. Priya Sharma", "", "Pending scrutiny"),
        ("EL-2026-002", "Recount Dispute - Delhi East", "Assembly", "Delhi", "Delhi East",
         "Supreme Court", "Amit Patel", "State Election Board", "2026-02-20", "2026-08-15",
         "In Progress", "High", "Adv. Vikram Singh", "", "Observer assigned"),
        ("EL-2026-003", "Booth Malpractice - Bangalore", "Assembly", "Karnataka", "Bangalore South",
         "Karnataka HC", "Sneha Reddy", "District Collector", "2026-03-05", "2026-07-22",
         "Pending Investigation", "Medium", "Adv. Karthik Iyer", "", "Evidence review"),
        ("EL-2026-004", "Vote Count Challenge - Chennai", "Parliamentary", "Tamil Nadu", "Chennai South",
         "Madras HC", "Karthik Iyer", "Returning Officer", "2025-11-10", "2026-06-30",
         "Closed", "Low", "Adv. Anita Desai", "", "Dismissed"),
        ("EL-2026-005", "EVM Tampering Allegation", "Assembly", "Telangana", "Hyderabad West",
         "Telangana HC", "Farhan Ali", "State CEO", "2026-04-01", "2026-09-05",
         "Open", "High", "Adv. Meera Nair", "", "High priority"),
    ]
    cur.executemany(
        """INSERT INTO litigation_cases
           (case_id, case_name, election_type, state, district, court, petitioner, respondent,
            filing_date, hearing_date, current_status, priority, advocate, documents, remarks)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        cases,
    )

    complaints = [
        ("CMP-2026-001", "Ravi Shankar", "Booth 42", "Mumbai North", "Booth Malpractice",
         "Unauthorized persons inside polling booth", "", "Officer Sharma", "Open", "", "", "High", ""),
        ("CMP-2026-002", "Lakshmi Devi", "Booth 18", "Delhi East", "Vote Counting",
         "Mismatch in EVM and VVPAT counts", "", "Officer Patel", "In Progress", "", "", "High", ""),
        ("CMP-2026-003", "Mohammed Khan", "Booth 7", "Bangalore South", "Agent Conduct",
         "Polling agent denied entry", "", "Officer Reddy", "Resolved", "Agent permitted", "2026-05-20", "Medium", ""),
        ("CMP-2026-004", "Anitha Raj", "Booth 31", "Chennai South", "Infrastructure",
         "Inadequate lighting at polling station", "", "Officer Iyer", "Open", "", "", "Low", ""),
    ]
    cur.executemany(
        """INSERT INTO complaints
           (complaint_id, complainant_name, booth, constituency, category, description,
            evidence_path, assigned_officer, status, resolution, resolution_date, priority, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        complaints,
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
        "INSERT INTO financial_transactions (transaction_id, txn_date, from_account, to_account, amount, approved_by) VALUES (?,?,?,?,?,?)",
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
        recovery = max(0, row[4] - expected)
        status = "Overcharge" if variance > 1 else "Undercharge" if variance < -1 else "OK"
        cur.execute(
            """INSERT INTO interest_validation
               (account, principal, rate, time_days, actual_interest, expected_interest, variance_pct, recovery_opportunity, status)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (row[0], row[1], row[2], row[3], row[4], expected, variance, recovery, status),
        )

    idle = [
        ("ACC-201", 850000, "2026-02-15", 130, "Sweep Account", 42500),
        ("ACC-202", 1200000, "2026-01-20", 156, "Invest in FD", 72000),
        ("ACC-203", 450000, "2026-04-01", 85, "Review Account", 18000),
    ]
    cur.executemany(
        "INSERT INTO idle_accounts (account, balance, last_transaction_date, idle_days, recommendation, projected_earnings) VALUES (?,?,?,?,?,?)",
        idle,
    )

    signatories = [
        ("ACC-001", "John Smith", "2027-12-31", 1, "Active"),
        ("ACC-002", "Jane Doe", "2027-12-31", 1, "Active"),
        ("ACC-003", "John Smith", "2026-01-01", 1, "Expired"),
        ("ACC-004", "John Smith", "2027-06-30", 1, "Active"),
        ("ACC-005", "Jane Doe", "2027-06-30", 1, "Active"),
    ]
    cur.executemany(
        "INSERT INTO signatories (account, authorized_signatory, expiry_date, dual_approval_required, status) VALUES (?,?,?,?,?)",
        signatories,
    )


def log_activity(username: str, role: str, action: str, module: str = "", details: str = "", ip: str = "") -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_logs (username, role, action, module, details, ip_address) VALUES (?,?,?,?,?,?)",
        (username, role, action, module, details, ip),
    )
    conn.commit()
    conn.close()


def log_audit(
    username: str, role: str, table_name: str, record_id: str, action: str,
    old_value: Any = None, new_value: Any = None, ip: str = "",
) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO audit_trail (username, role, table_name, record_id, action, old_value, new_value, ip_address)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            username, role, table_name, record_id, action,
            json.dumps(old_value) if old_value is not None else None,
            json.dumps(new_value) if new_value is not None else None,
            ip,
        ),
    )
    conn.commit()
    conn.close()


# --- Litigation Cases ---

def get_litigation_cases(
    search: str = "", status: str = "", state: str = "", court: str = "", priority: str = "",
) -> pd.DataFrame:
    query = "SELECT * FROM litigation_cases WHERE 1=1"
    params: list[Any] = []
    if search:
        query += " AND (case_id LIKE ? OR case_name LIKE ? OR petitioner LIKE ? OR court LIKE ?)"
        params.extend([f"%{search}%"] * 4)
    if status and status != "All":
        query += " AND current_status = ?"
        params.append(status)
    if state and state != "All":
        query += " AND state = ?"
        params.append(state)
    if court and court != "All":
        query += " AND court = ?"
        params.append(court)
    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)
    query += " ORDER BY created_at DESC"
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return _rows_to_df(rows)


def create_litigation_case(data: dict, user: str, role: str) -> bool:
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO litigation_cases
               (case_id, case_name, election_type, state, district, court, petitioner, respondent,
                filing_date, hearing_date, current_status, priority, advocate, documents, remarks)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data["case_id"], data["case_name"], data.get("election_type"), data.get("state"),
                data.get("district"), data.get("court"), data.get("petitioner"), data.get("respondent"),
                data.get("filing_date"), data.get("hearing_date"), data.get("current_status", "Open"),
                data.get("priority", "Medium"), data.get("advocate"), data.get("documents"), data.get("remarks"),
            ),
        )
        conn.commit()
        log_audit(user, role, "litigation_cases", data["case_id"], "CREATE", new_value=data)
        log_activity(user, role, "Created case", "Litigation", data["case_id"])
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_litigation_case(case_id: str, data: dict, user: str, role: str) -> None:
    conn = get_connection()
    old = conn.execute("SELECT * FROM litigation_cases WHERE case_id = ?", (case_id,)).fetchone()
    conn.execute(
        """UPDATE litigation_cases SET
           case_name=?, election_type=?, state=?, district=?, court=?, petitioner=?, respondent=?,
           filing_date=?, hearing_date=?, current_status=?, priority=?, advocate=?, documents=?, remarks=?,
           updated_at=CURRENT_TIMESTAMP WHERE case_id=?""",
        (
            data.get("case_name"), data.get("election_type"), data.get("state"), data.get("district"),
            data.get("court"), data.get("petitioner"), data.get("respondent"),
            data.get("filing_date"), data.get("hearing_date"), data.get("current_status"),
            data.get("priority"), data.get("advocate"), data.get("documents"), data.get("remarks"), case_id,
        ),
    )
    conn.commit()
    conn.close()
    log_audit(user, role, "litigation_cases", case_id, "UPDATE", dict(old) if old else None, data)


def delete_litigation_case(case_id: str, user: str, role: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM litigation_cases WHERE case_id = ?", (case_id,))
    conn.commit()
    conn.close()
    log_audit(user, role, "litigation_cases", case_id, "DELETE")
    log_activity(user, role, "Deleted case", "Litigation", case_id)


# --- Complaints ---

def get_complaints(search: str = "", status: str = "", category: str = "") -> pd.DataFrame:
    query = "SELECT * FROM complaints WHERE 1=1"
    params: list[Any] = []
    if search:
        query += " AND (complaint_id LIKE ? OR complainant_name LIKE ? OR constituency LIKE ?)"
        params.extend([f"%{search}%"] * 3)
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY created_at DESC"
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return _rows_to_df(rows)


def create_complaint(data: dict, user: str, role: str) -> bool:
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO complaints
               (complaint_id, complainant_name, booth, constituency, category, description,
                evidence_path, assigned_officer, status, resolution, resolution_date, priority, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data["complaint_id"], data["complainant_name"], data.get("booth"), data.get("constituency"),
                data.get("category"), data.get("description"), data.get("evidence_path"),
                data.get("assigned_officer"), data.get("status", "Open"), data.get("resolution"),
                data.get("resolution_date"), data.get("priority", "Medium"), data.get("notes"),
            ),
        )
        conn.commit()
        log_audit(user, role, "complaints", data["complaint_id"], "CREATE", new_value=data)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_complaint(complaint_id: str, data: dict, user: str, role: str) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE complaints SET
           complainant_name=?, booth=?, constituency=?, category=?, description=?,
           assigned_officer=?, status=?, resolution=?, resolution_date=?, priority=?, notes=?,
           updated_at=CURRENT_TIMESTAMP WHERE complaint_id=?""",
        (
            data.get("complainant_name"), data.get("booth"), data.get("constituency"),
            data.get("category"), data.get("description"), data.get("assigned_officer"),
            data.get("status"), data.get("resolution"), data.get("resolution_date"),
            data.get("priority"), data.get("notes"), complaint_id,
        ),
    )
    conn.commit()
    conn.close()
    log_audit(user, role, "complaints", complaint_id, "UPDATE", new_value=data)


def delete_complaint(complaint_id: str, user: str, role: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM complaints WHERE complaint_id = ?", (complaint_id,))
    conn.commit()
    conn.close()
    log_audit(user, role, "complaints", complaint_id, "DELETE")


# --- Financial Transactions ---

def get_transactions(search: str = "") -> pd.DataFrame:
    query = "SELECT * FROM financial_transactions WHERE 1=1"
    params: list[Any] = []
    if search:
        query += " AND (transaction_id LIKE ? OR from_account LIKE ? OR to_account LIKE ?)"
        params.extend([f"%{search}%"] * 3)
    query += " ORDER BY txn_date DESC"
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return _rows_to_df(rows)


def bulk_insert_transactions(df: pd.DataFrame, user: str, role: str) -> int:
    conn = get_connection()
    count = 0
    for _, row in df.iterrows():
        conn.execute(
            """INSERT INTO financial_transactions (transaction_id, txn_date, from_account, to_account, amount, approved_by)
               VALUES (?,?,?,?,?,?)""",
            (
                str(row.get("Transaction ID", row.get("transaction_id", f"TXN-{count}"))),
                str(row.get("Date", row.get("txn_date", ""))),
                str(row.get("From Account", row.get("from_account", ""))),
                str(row.get("To Account", row.get("to_account", ""))),
                float(row.get("Amount", row.get("amount", 0))),
                str(row.get("Approved By", row.get("approved_by", ""))),
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    log_activity(user, role, f"Imported {count} transactions", "Upload")
    return count


def update_transaction_risk(txn_id: str, risk_score: float, pattern: str, remarks: str, risk_level: str = "") -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE financial_transactions SET risk_score=?, pattern=?, remarks=?, risk_level=? WHERE transaction_id=?",
        (risk_score, pattern, remarks, risk_level, txn_id),
    )
    conn.commit()
    conn.close()


# --- Interest / Idle / Signatories ---

def get_interest_validations() -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM interest_validation ORDER BY created_at DESC").fetchall()
    conn.close()
    return _rows_to_df(rows)


def bulk_insert_interest(df: pd.DataFrame, user: str, role: str) -> int:
    conn = get_connection()
    count = 0
    for _, row in df.iterrows():
        principal = float(row.get("Principal", row.get("principal", 0)))
        rate = float(row.get("Rate", row.get("rate", 0)))
        time_days = float(row.get("Time Days", row.get("time_days", 365)))
        actual = float(row.get("Actual Interest", row.get("actual_interest", 0)))
        expected = principal * rate * (time_days / 365)
        variance = ((actual - expected) / expected * 100) if expected else 0
        recovery = max(0, actual - expected)
        status = "Overcharge" if variance > 1 else "Undercharge" if variance < -1 else "OK"
        conn.execute(
            """INSERT INTO interest_validation
               (account, principal, rate, time_days, actual_interest, expected_interest, variance_pct, recovery_opportunity, status)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (str(row.get("Account", row.get("account", ""))), principal, rate, time_days, actual, expected, variance, recovery, status),
        )
        count += 1
    conn.commit()
    conn.close()
    log_activity(user, role, f"Imported {count} interest records", "Bank Charges")
    return count


def get_idle_accounts() -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM idle_accounts ORDER BY idle_days DESC").fetchall()
    conn.close()
    return _rows_to_df(rows)


def bulk_insert_idle(df: pd.DataFrame, idle_threshold: int, balance_threshold: float, user: str, role: str) -> int:
    conn = get_connection()
    count = 0
    today = datetime.now()
    for _, row in df.iterrows():
        account = str(row.get("Account", row.get("account", "")))
        balance = float(row.get("Balance", row.get("balance", 0)))
        last_date_str = str(row.get("Last Transaction Date", row.get("last_transaction_date", "")))
        try:
            last_date = datetime.strptime(last_date_str[:10], "%Y-%m-%d")
            idle_days = (today - last_date).days
        except ValueError:
            idle_days = 0
        if idle_days >= idle_threshold and balance >= balance_threshold:
            projected = balance * 0.05 * (idle_days / 365)
            rec = "Invest in FD" if balance > 1000000 else "Sweep Account" if balance > 500000 else "Review Account"
            conn.execute(
                "INSERT INTO idle_accounts (account, balance, last_transaction_date, idle_days, recommendation, projected_earnings) VALUES (?,?,?,?,?,?)",
                (account, balance, last_date_str, idle_days, rec, projected),
            )
            count += 1
    conn.commit()
    conn.close()
    log_activity(user, role, f"Flagged {count} idle accounts", "Idle Funds")
    return count


def get_signatories() -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM signatories").fetchall()
    conn.close()
    return _rows_to_df(rows)


def bulk_insert_signatories(df: pd.DataFrame, user: str, role: str) -> int:
    conn = get_connection()
    count = 0
    for _, row in df.iterrows():
        conn.execute(
            "INSERT INTO signatories (account, authorized_signatory, expiry_date, dual_approval_required, status) VALUES (?,?,?,?,?)",
            (
                str(row.get("Account", row.get("account", ""))),
                str(row.get("Authorized Signatory", row.get("authorized_signatory", ""))),
                str(row.get("Expiry Date", row.get("expiry_date", ""))),
                int(row.get("Dual Approval", row.get("dual_approval_required", 1))),
                str(row.get("Status", row.get("status", "Active"))),
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    log_activity(user, role, f"Imported {count} signatories", "Signatory")
    return count


def save_uploaded_file(filename: str, filepath: str, file_type: str, module: str, user: str, row_count: int = 0) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO uploaded_files (filename, filepath, file_type, module, uploaded_by, row_count) VALUES (?,?,?,?,?,?)",
        (filename, filepath, file_type, module, user, row_count),
    )
    conn.commit()
    conn.close()
    log_activity(user, "", "Upload", module, filename)


def get_uploaded_files() -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM uploaded_files ORDER BY created_at DESC").fetchall()
    conn.close()
    return _rows_to_df(rows)


def get_activity_logs(limit: int = 50) -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return _rows_to_df(rows)


def get_audit_trail(limit: int = 50) -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM audit_trail ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return _rows_to_df(rows)


def get_dashboard_kpis() -> dict[str, int | float]:
    conn = get_connection()
    total_cases = conn.execute("SELECT COUNT(*) FROM litigation_cases").fetchone()[0]
    open_cases = conn.execute(
        "SELECT COUNT(*) FROM litigation_cases WHERE current_status NOT IN ('Closed', 'Dismissed')"
    ).fetchone()[0]
    closed_cases = conn.execute(
        "SELECT COUNT(*) FROM litigation_cases WHERE current_status IN ('Closed', 'Dismissed')"
    ).fetchone()[0]
    pending_inv = conn.execute(
        "SELECT COUNT(*) FROM litigation_cases WHERE current_status = 'Pending Investigation'"
    ).fetchone()[0]
    high_risk = conn.execute(
        "SELECT COUNT(*) FROM litigation_cases WHERE priority = 'High'"
    ).fetchone()[0]
    total_complaints = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    financial_alerts = conn.execute(
        "SELECT COUNT(*) FROM financial_transactions WHERE risk_score >= 60"
    ).fetchone()[0] + conn.execute(
        "SELECT COUNT(*) FROM interest_validation WHERE status != 'OK'"
    ).fetchone()[0]
    suspicious = conn.execute(
        "SELECT COUNT(*) FROM financial_transactions WHERE risk_score >= 60"
    ).fetchone()[0]
    idle_count = conn.execute("SELECT COUNT(*) FROM idle_accounts").fetchone()[0]
    interest_dev = conn.execute("SELECT COUNT(*) FROM interest_validation WHERE status != 'OK'").fetchone()[0]

    compliance_score = max(0, 100 - (suspicious * 5 + interest_dev * 3 + high_risk * 2))

    kpis = {
        "total_cases": total_cases,
        "open_cases": open_cases,
        "closed_cases": closed_cases,
        "pending_investigation": pending_inv,
        "high_risk_cases": high_risk,
        "total_complaints": total_complaints,
        "financial_alerts": financial_alerts,
        "compliance_score": compliance_score,
        "transactions_analyzed": conn.execute("SELECT COUNT(*) FROM financial_transactions").fetchone()[0],
        "suspicious_transactions": suspicious,
        "idle_balances": idle_count,
        "interest_deviations": interest_dev,
    }
    conn.close()
    return kpis


def global_search(query: str) -> dict[str, pd.DataFrame]:
    if not query:
        return {}
    return {
        "cases": get_litigation_cases(search=query),
        "complaints": get_complaints(search=query),
        "transactions": get_transactions(search=query),
    }
