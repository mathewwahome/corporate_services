import frappe

@frappe.whitelist()
def get_user_roles():
    return frappe.get_roles(frappe.session.user)
