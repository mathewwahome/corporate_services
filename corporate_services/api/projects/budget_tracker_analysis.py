import frappe
from frappe.utils import getdate, add_months
from datetime import timedelta
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def budget_calc(docname):
    project_doc = frappe.get_doc("Project", docname)
    try:
        budget_calc_time =project_doc.actual_time
        
        child = project_doc.getone('custom_budget_tracker_analysis')
        
        
        
        rate = flt(child.rate) 
        daysunits = flt(child.daysunits)
        cost = rate * daysunits
        
        amount_received =  cost  * 0.4
        actual_expence = 
        
        
        
        frappe.throw(_("The try catch function for the Project budget tracker {0}.").format(amount_received))
              
        return {
            'projects': project_doc,
            'daysunits': budget_calc_time
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching projects budget tracker: {str(e)}", "budget_calc")
        return []
