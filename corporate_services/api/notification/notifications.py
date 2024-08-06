import frappe
from frappe.utils import get_url_to_form


   

    

def employee_grievance(doc, method):
    if doc.workflow_state == "Approved by HR":

        owner_email = frappe.db.get_value("User", doc.owner, "email")
        
        subject = "Your document has been approved by HR"
        message = f"Hello,\n\nYour Grievance {doc.name} has been received and approved by HR.\n\nBest Regards,\n\n HR"
        
        frappe.sendmail(
            recipients=[owner_email],
            subject=subject,
            message=message
        )
        
        
def alert_supervisor_asset_requisition(doc, method):
    
    if doc.workflow_state == "Submitted to Supervisor":
        
        employee_id = doc.requested_by
        employee = frappe.get_doc("Employee", employee_id)
        
        if employee.reports_to:
            supervisor_id = employee.reports_to
            supervisor = frappe.get_doc("Employee", supervisor_id)
            
            supervisor_email = supervisor.company_email or supervisor.personal_email
            message = """
                Dear {},\n\n
    
                I have submitted my {} for your review and approval.\n\n
            
                Kind regards,
                
                {}
                """.format(supervisor.employee_name, doc.doctype, employee.employee_name)
            
            frappe.sendmail(
                recipients=[supervisor_email],
                subject=frappe._('Asset Custodianship Requisition Submission from {}'.format(employee.employee_name)),
                message=message,
            )
            

            
            


def send_email(recipients, subject, message, pdf_content, doc_name):
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        attachments=[{
            'fname': '{}.pdf'.format(doc_name),
            'fcontent': pdf_content
        }],
        header=("Work Continuity Plan Submission", "text/html")
    )

doc_events = {
    "Employee Grievance": {
        "on_update": employee_grievance
    },
   
    "Leave Application":{
        "on_update": alert_supervisor_leave_application
    },
    "Asset Custodianship Requisition":{
        "on_update": alert_supervisor_asset_requisition
    },
}