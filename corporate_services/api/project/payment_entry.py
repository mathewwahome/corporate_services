import frappe
from frappe import _

def fetch_payments(doc, method=None):
    try:
        if isinstance(doc, dict):
            doc = frappe.get_doc("Project", doc.get("name"))
            
        # Get Project DocType metadata to find the child table field
        project_meta = frappe.get_meta("Project")
        
        # Log the available table fields for debugging
        table_fields = project_meta.get_table_fields()
        
        
        # Fetch payment entries
        payments = frappe.get_all(
            "Payment Entry",
            filters={
                "docstatus": 1,
                "project": doc.name if hasattr(doc, 'name') else None
            },
            fields=[
                "name",
                "payment_type",
                "paid_amount",
                "received_amount",
                "party_type",
                "party",
                "custom_total_cost"
            ]
        )

        # Get fresh copy of project
        project = frappe.get_doc("Project", doc.name)
        
        # Fetch and prepare all budget lines first
        budget_lines = []
        for payment in payments:
            child_rows = frappe.get_all(
                'Budget Line Template',
                filters={'parent': payment.name},
                fields=['unit_loe_type','budget_line','unit_loe', 'rate', 'cost']
            )
            
            budget_lines.extend(child_rows)

        # Find the correct child table field
        child_table_field = None
        for field in table_fields:
            if "budget" in field.fieldname.lower():
                child_table_field = field.fieldname
                break
        
        if not child_table_field:
            frappe.throw(_("Could not find budget line child table in Project DocType"))

        # Clear and update the child table
        project.set(child_table_field, [])
        
        for row in budget_lines:
            project.append(child_table_field, {
                'budget_line':row.budget_line,
                'unit_loe_type':row.unit_loe_type,
                'unit_loe': row.unit_loe,
                'rate': row.rate,
                'cost': row.cost
            })

        # Save with flags
        project.flags.ignore_permissions = True
        project.flags.ignore_validate = True
        project.flags.ignore_mandatory = True
        project.save()
        
        frappe.db.commit()
        

    except Exception as e:
        frappe.log_error(
            message=f"Error in fetch_payments: {str(e)}\nProject: {doc.name}\nFull traceback: {frappe.get_traceback()}",
            title="Budget Line Update Error"
        )
        frappe.db.rollback()