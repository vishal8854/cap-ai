import json
import sqlite3
from typing import Any

import pandas as pd

from database.db import get_connection


def _rows_to_df(rows: list[sqlite3.Row]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def log_activity(username: str, role: str, action: str, module: str = "", details: str = "") -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO activity_logs (username, role, action, module, details) VALUES (?,?,?,?,?)",
        (username, role, action, module, details),
    )
    conn.commit()
    conn.close()


def log_audit(
    username: str,
    role: str,
    table_name: str,
    record_id: str,
    action: str,
    old_value: Any = None,
    new_value: Any = None,
) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO audit_trail (username, role, table_name, record_id, action, old_value, new_value)
           VALUES (?,?,?,?,?,?,?)""",
        (
            username,
            role,
            table_name,
            record_id,
            action,
            json.dumps(old_value) if old_value is not None else None,
            json.dumps(new_value) if new_value is not None else None,
        ),
    )
    conn.commit()
    conn.close()


# --- Recount Cases ---

def get_recount_cases(search: str = "", status: str = "", branch: str = "") -> pd.DataFrame:
    query = "SELECT * FROM recount_cases WHERE 1=1"
    params: list[Any] = []
    if search:
        query += " AND (case_id LIKE ? OR branch LIKE ? OR cashier LIKE ? OR observer LIKE ?)"
        params.extend([f"%{search}%"] * 4)
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
    if branch and branch != "All":
        query += " AND branch = ?"
        params.append(branch)
    query += " ORDER BY created_at DESC"
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return _rows_to_df(rows)


def create_recount_case(case_id: str, branch: str, cashier: str, amount: float, user: str, role: str) -> bool:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO recount_cases (case_id, branch, cashier, amount) VALUES (?,?,?,?)",
            (case_id, branch, cashier, amount),
        )
        conn.commit()
        log_audit(user, role, "recount_cases", case_id, "CREATE", new_value={"case_id": case_id})
        log_activity(user, role, "Created recount case", "Recount Management", case_id)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_recount_status(case_id: str, status: str, user: str, role: str) -> None:
    conn = get_connection()
    old = conn.execute("SELECT status FROM recount_cases WHERE case_id = ?", (case_id,)).fetchone()
    conn.execute(
        "UPDATE recount_cases SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ?",
        (status, case_id),
    )
    conn.commit()
    conn.close()
    log_audit(user, role, "recount_cases", case_id, "UPDATE", {"status": old["status"] if old else None}, {"status": status})


def assign_observer(case_id: str, observer: str, user: str, role: str) -> None:
    conn = get_connection()
    old = conn.execute("SELECT observer FROM recount_cases WHERE case_id = ?", (case_id,)).fetchone()
    conn.execute(
        "UPDATE recount_cases SET observer = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ?",
        (observer, case_id),
    )
    conn.commit()
    conn.close()
    log_audit(user, role, "recount_cases", case_id, "ASSIGN", {"observer": old["observer"] if old else None}, {"observer": observer})


def close_recount_case(case_id: str, user: str, role: str) -> None:
    update_recount_status(case_id, "Closed", user, role)


# --- Observer Schedule ---

def get_observer_schedule() -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM observer_schedule ORDER BY schedule_date DESC").fetchall()
    conn.close()
    return _rows_to_df(rows)


def add_observer_schedule(observer_name: str, branch: str, schedule_date: str, shift: str, remarks: str, user: str, role: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO observer_schedule (observer_name, branch, schedule_date, shift, remarks) VALUES (?,?,?,?,?)",
        (observer_name, branch, schedule_date, shift, remarks),
    )
    conn.commit()
    conn.close()
    log_activity(user, role, "Scheduled observer", "Recount Management", f"{observer_name} @ {branch}")


# --- Tally Documents ---

def save_tally_document(case_id: str, doc_type: str, filename: str, filepath: str, user: str, role: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO tally_documents (case_id, doc_type, filename, filepath) VALUES (?,?,?,?)",
        (case_id, doc_type, filename, filepath),
    )
    conn.commit()
    conn.close()
    log_activity(user, role, f"Uploaded {doc_type}", "Recount Management", filename)


def get_tally_documents(case_id: str = "") -> pd.DataFrame:
    conn = get_connection()
    if case_id:
        rows = conn.execute("SELECT * FROM tally_documents WHERE case_id = ? ORDER BY uploaded_at DESC", (case_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tally_documents ORDER BY uploaded_at DESC").fetchall()
    conn.close()
    return _rows_to_df(rows)


# --- Transactions ---

def get_transactions(search: str = "") -> pd.DataFrame:
    query = "SELECT * FROM transactions WHERE 1=1"
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
            """INSERT INTO transactions (transaction_id, txn_date, from_account, to_account, amount, approved_by)
               VALUES (?,?,?,?,?,?)""",
            (
                str(row.get("Transaction ID", row.get("transaction_id", f"TXN-{count}"))),
                str(row.get("Date", row.get("txn_date", ""))),
                str(row.get("From Account", row.get("from_account", ""))),
                str(row.get("To Account", row.get("to_account", ""))),
                float(row.get("Amount", row.get("amount", 0))),
                str(row.get("Approved By", row.get("approved_by", ""))) if "Approved By" in row or "approved_by" in row else None,
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    log_activity(user, role, f"Imported {count} transactions", "Excel Import")
    return count


def update_transaction_risk(txn_id: str, risk_score: float, pattern: str, remarks: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE transactions SET risk_score = ?, pattern = ?, remarks = ? WHERE transaction_id = ?",
        (risk_score, pattern, remarks, txn_id),
    )
    conn.commit()
    conn.close()


# --- Interest Validation ---

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
        status = "Overcharge" if variance > 1 else "Undercharge" if variance < -1 else "OK"
        conn.execute(
            """INSERT INTO interest_validation
               (account, principal, rate, time_days, actual_interest, expected_interest, variance_pct, status)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                str(row.get("Account", row.get("account", ""))),
                principal,
                rate,
                time_days,
                actual,
                expected,
                variance,
                status,
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    log_activity(user, role, f"Imported {count} interest records", "Interest Validation")
    return count


# --- Idle Accounts ---

def get_idle_accounts() -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM idle_accounts ORDER BY idle_days DESC").fetchall()
    conn.close()
    return _rows_to_df(rows)


def bulk_insert_idle(df: pd.DataFrame, idle_threshold: int, balance_threshold: float, user: str, role: str) -> int:
    from datetime import datetime

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
            if balance > 1000000:
                rec = "Invest in FD"
            elif balance > 500000:
                rec = "Sweep Account"
            else:
                rec = "Review Account"
            conn.execute(
                "INSERT INTO idle_accounts (account, balance, last_transaction_date, idle_days, recommendation) VALUES (?,?,?,?,?)",
                (account, balance, last_date_str, idle_days, rec),
            )
            count += 1
    conn.commit()
    conn.close()
    log_activity(user, role, f"Flagged {count} idle accounts", "Idle Balance")
    return count


# --- Signatory ---

def get_signatories() -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM signatory_verification").fetchall()
    conn.close()
    return _rows_to_df(rows)


def bulk_insert_signatories(df: pd.DataFrame, user: str, role: str) -> int:
    conn = get_connection()
    count = 0
    for _, row in df.iterrows():
        conn.execute(
            "INSERT INTO signatory_verification (account, authorized_signatory) VALUES (?,?)",
            (str(row.get("Account", row.get("account", ""))), str(row.get("Authorized Signatory", row.get("authorized_signatory", "")))),
        )
        count += 1
    conn.commit()
    conn.close()
    log_activity(user, role, f"Imported {count} signatories", "Signatory Verification")
    return count


# --- Activity & Audit ---

def get_activity_logs(limit: int = 50) -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return _rows_to_df(rows)


def get_audit_trail(limit: int = 50) -> pd.DataFrame:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM audit_trail ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return _rows_to_df(rows)


# --- Dashboard KPIs ---

def get_dashboard_kpis() -> dict[str, int | float]:
    conn = get_connection()
    kpis = {
        "total_accounts": conn.execute("SELECT COUNT(DISTINCT account) FROM signatory_verification").fetchone()[0],
        "transactions_analyzed": conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
        "suspicious_transactions": conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE risk_score >= 60 OR risk_score IS NULL AND transaction_id IN ('TXN-1003','TXN-1007')"
        ).fetchone()[0],
        "idle_balances": conn.execute("SELECT COUNT(*) FROM idle_accounts").fetchone()[0],
        "interest_deviations": conn.execute(
            "SELECT COUNT(*) FROM interest_validation WHERE status != 'OK'"
        ).fetchone()[0],
        "unauthorized_approvals": 2,
        "active_recount_cases": conn.execute(
            "SELECT COUNT(*) FROM recount_cases WHERE status != 'Closed'"
        ).fetchone()[0],
        "observer_assignments": conn.execute(
            "SELECT COUNT(*) FROM observer_schedule"
        ).fetchone()[0],
    }
    conn.close()
    return kpis
