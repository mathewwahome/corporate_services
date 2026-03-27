import frappe


def get_default_print_format(doctype):
    return (
        frappe.db.get_value(
            "Property Setter",
            {"doc_type": doctype, "property": "default_print_format"},
            "value",
        )
        or frappe.db.get_value(
            "Print Format",
            {"doc_type": doctype},
            "name",
        )
        or "Standard"
    )

