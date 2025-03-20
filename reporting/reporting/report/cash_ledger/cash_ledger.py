
import frappe
from frappe.utils import flt

def execute(filters=None):
    filters = frappe._dict(filters or {})
    data, columns = get_columns(), get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Date", "fieldname": "debit_date", "fieldtype": "Date", "width": 100},
        {"label": "Account Credited", "fieldname": "debit_account", "fieldtype": "Data", "width": 150},
        {"label": "Description", "fieldname": "debit_description", "fieldtype": "Data", "width": 200},
        {"label": "Debit (Rs.)", "fieldname": "debit_amount", "fieldtype": "Currency", "width": 100},
        {"label": "Date", "fieldname": "credit_date", "fieldtype": "Date", "width": 100},
        {"label": "Account Debited", "fieldname": "credit_account", "fieldtype": "Data", "width": 150},
        {"label": "Description", "fieldname": "credit_description", "fieldtype": "Data", "width": 200},
        {"label": "Credit (Rs.)", "fieldname": "credit_amount", "fieldtype": "Currency", "width": 100},
    ]

def get_data(filters):
    # Fetch Opening Balance
    opening_balance = get_opening_balance(filters)
    data = [
        {
            "debit_date": None,
            "debit_account": None,
            "debit_description": "Opening Balance of the Period",
            "debit_amount": opening_balance,
            "credit_date": None,
            "credit_account": None,
            "credit_description": None,
            "credit_amount": None,
        }
    ]

    # Fetch General Ledger Entries
    general_ledger_entries = frappe.db.sql(
        """
        SELECT 
            posting_date, account, debit, credit, remarks 
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND account_type = 'Cash'
        ORDER BY posting_date
        """,
        filters,
        as_dict=True,
    )

    # Process entries
    for entry in general_ledger_entries:
        data.append({
            "debit_date": entry.posting_date if entry.debit > 0 else None,
            "debit_account": entry.account if entry.debit > 0 else None,
            "debit_description": entry.remarks if entry.debit > 0 else None,
            "debit_amount": flt(entry.debit),
            "credit_date": entry.posting_date if entry.credit > 0 else None,
            "credit_account": entry.account if entry.credit > 0 else None,
            "credit_description": entry.remarks if entry.credit > 0 else None,
            "credit_amount": flt(entry.credit),
        })

    # Add Closing Balance
    closing_balance = opening_balance + sum([entry['debit'] - entry['credit'] for entry in general_ledger_entries])
    data.append({
        "debit_date": None,
        "debit_account": None,
        "debit_description": None,
        "debit_amount": None,
        "credit_date": None,
        "credit_account": None,
        "credit_description": "Closing Balance of the Period",
        "credit_amount": closing_balance,
    })

    return data

def get_opening_balance(filters):
    opening_balance = frappe.db.sql("""
        SELECT SUM(debit - credit)
        FROM `tabGL Entry`
        WHERE posting_date < %(from_date)s AND account_type = 'Cash'
    """, filters)[0][0] or 0
    return flt(opening_balance)
