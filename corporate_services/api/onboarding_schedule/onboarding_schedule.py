import frappe

def notify_selected_staff(doc, method):
    """
    Hook: called on_update of the Applicant document. 
    When status changes to 'Selected', tick the staff_selection checkbox on the linked Onboarding document.
    """
    
    if doc.status != "Selected":
        return

    # Avoid re-running if status hasn't changed
    before = doc.get_doc_before_save()
    if before and before.get("status") == "Selected":
        return

    # Find the linked Onboarding document
    onboarding_name = frappe.db.get_value(
        "Onboarding",
        {"applicant": doc.name},
        "name"
    )

    if not onboarding_name:
        frappe.log_error(
            f"No Onboarding record found for applicant: {doc.name}",
            "Onboarding Staff Selection Error"
        )
        return

    # Tick the checkbox
    frappe.db.set_value(
        "Onboarding",
        onboarding_name,
        "staff_selection",
        1
    )

    frappe.msgprint(
        f"Staff Selection marked on Onboarding: {onboarding_name}",
        indicator="green",
        alert=True
    )
