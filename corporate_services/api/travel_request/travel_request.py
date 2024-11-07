import frappe

@frappe.whitelist()
def get_per_diem_rates(place):
    if not frappe.has_permission("Per Diem Rates Child Table", "read"):
        frappe.throw("You do not have permission to access this resource.")
    
    return frappe.get_all("Per Diem Rates Child Table", 
                      filters={"place_of_travel": place}, 
                      fields=["place_of_travel", "accommodation_max", "accommodation_min", 
                              "meal_incidentals_expenses_max", "meal_incidentals_expenses_min"])


@frappe.whitelist()
def get_travel_request_costs(travel_request):
    if not frappe.has_permission("Travel Request", "read"):
        frappe.throw("You do not have permission to access this resource.")

    # Fetch main travel request fields
    travel_request_data = frappe.get_all("Travel Request", 
                                         filters={"name": travel_request}, 
                                         fields=["name", "employee", "purpose_of_travel", "custom_expected_support"])

    # Fetch child table data
    child_table_data = frappe.get_all("Travel Request Activity Participants", 
                                      filters={"parent": travel_request, "parenttype": "Travel Request"},
                                      fields=["units", "pax", "rate", "total"])

    return {
        "travel_request_data": travel_request_data,
        "custom_activity_participants_table": child_table_data
    }
