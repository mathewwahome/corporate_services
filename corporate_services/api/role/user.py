import frappe

@frappe.whitelist()
def get_finance_employees():
    users = frappe.get_all('Has Role', filters={'role': 'Finance'}, fields=['parent'], ignore_permissions=True)
    user_ids = [user['parent'] for user in users]

    if user_ids:
        employees = frappe.get_all('Employee', filters={'user_id': ['in', user_ids]}, fields=['name'], ignore_permissions=True)
        return [emp['name'] for emp in employees]
    return []
