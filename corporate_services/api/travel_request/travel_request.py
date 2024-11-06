import frappe

@frappe.whitelist()
def get_per_diem_rates(place):
    if not frappe.has_permission("Per Diem Rates Child Table", "read"):
        frappe.throw("You do not have permission to access this resource.")
    
    return frappe.get_all("Per Diem Rates Child Table", 
                      filters={"place_of_travel": place}, 
                      fields=["place_of_travel", "accommodation_max", "accommodation_min", 
                              "meal_incidentals_expenses_max", "meal_incidentals_expenses_min"])
