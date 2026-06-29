import pandas as pd

from database import crud


def verify_signatories(transactions_df: pd.DataFrame | None = None, signatories_df: pd.DataFrame | None = None) -> pd.DataFrame:
    if signatories_df is None:
        signatories_df = crud.get_signatories()
    if transactions_df is None:
        transactions_df = crud.get_transactions()

    if signatories_df.empty or transactions_df.empty:
        return pd.DataFrame(columns=["Account", "Transaction", "Issue"])

    auth_map = dict(zip(signatories_df["account"], signatories_df["authorized_signatory"]))
    issues = []

    for _, txn in transactions_df.iterrows():
        txn_id = txn.get("transaction_id", txn.get("Transaction ID", ""))
        approved_by = txn.get("approved_by", txn.get("Approved By", ""))
        from_acc = txn.get("from_account", txn.get("From Account", ""))
        to_acc = txn.get("to_account", txn.get("To Account", ""))

        for account in [from_acc, to_acc]:
            if not account or account not in auth_map:
                continue
            authorized = auth_map[account]
            if not approved_by:
                issues.append({"Account": account, "Transaction": txn_id, "Issue": "Missing Approval"})
            elif approved_by != authorized:
                issues.append({"Account": account, "Transaction": txn_id, "Issue": f"Unauthorized: {approved_by} (expected {authorized})"})

    return pd.DataFrame(issues)
