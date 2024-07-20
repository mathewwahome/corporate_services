import frappe
from frappe.utils import get_url_to_form

def alert_supervisor_travel_request(doc, method):
    if doc.workflow_state == "Submitted to Supervisor":
        
        employee_id = doc.employee
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
                subject=frappe._('Travel Request Submission from {}'.format(employee.employee_name)),
                message=message,
            )




def alert_supervisor_leave_application(doc, method):
    
    if doc.workflow_state == "Submitted to Supervisor":
        employee = frappe.get_doc("Employee", doc.employee)

        supervisor_id = employee.reports_to

        if supervisor_id:
            supervisor = frappe.get_doc("Employee", supervisor_id)
            supervisor_email = frappe.db.get_value("User", supervisor.user_id, "email")

            subject = "Leave Application Submitted"
            message = f"""
                Dear {supervisor.employee_name},\n\n

                I have applied for leave starting from {doc.from_date} to {doc.to_date}. Please review and approve it accordingly.\n\n

                Kind regards,

                {employee.employee_name}
                """

            frappe.sendmail(
                recipients=[supervisor_email],
                subject=subject,
                message=message
            )

   

    

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

def alert_supervisor_work_continuity_plan_submission(doc, method):
    if doc.workflow_state in ["Submitted to Supervisor", "Submitted to HR","Rejected By HR","Approved by HR","Rejected By Supervisor"]:
        
        employee_id = doc.employee
        employee = frappe.get_doc("Employee", employee_id)
        employee_email = employee.company_email or employee.personal_email

        doctype_url = get_url_to_form(doc.doctype, doc.name)
        print_format = "Standard"
        pdf_content = frappe.get_print(doc.doctype, doc.name, print_format, as_pdf=True)

        if doc.workflow_state == "Submitted to Supervisor":
            if employee.reports_to:
                supervisor_id = employee.reports_to
                supervisor = frappe.get_doc("Employee", supervisor_id)
                supervisor_email = supervisor.company_email or supervisor.personal_email
                
                message = """
                    Dear {},<br><br>
                    I have submitted my {} for your review and approval. You can view it <a href="{}">here</a>.<br><br>
                    Kind regards,<br>
                    {}
                """.format(supervisor.employee_name, doc.doctype, doctype_url, employee.employee_name)
                
                send_email(
                    recipients=[supervisor_email],
                    subject=frappe._('Work Continuity Plan Submission from {}'.format(employee.employee_name)),
                    message=message,
                    pdf_content=pdf_content,
                    doc_name=doc.name
                )
        elif doc.workflow_state == "Rejected By Supervisor":

                message_to_employee = """
                Dear {},<br><br>
                Your {} has been reviewed and unfortunately, it has been rejected. You can view the details <a href="{}">here</a>.<br><br>
                Kind regards,<br>
                Supervisor
                """.format(employee.employee_name, doc.doctype, doctype_url)
                    
                send_email(
                    recipients=[employee_email],
                    subject=frappe._('Your Work Continuity Plan has been Rejected'),
                    message=message_to_employee,
                    pdf_content=pdf_content,
                    doc_name=doc.name
                )  
                
        elif doc.workflow_state == "Submitted to HR":
            hr_managers = frappe.get_all('Has Role', filters={'role': 'HR Manager'}, fields=['parent'])
            hr_manager_emails = [frappe.get_value('User', hr_manager.parent, 'email') for hr_manager in hr_managers]

            message = """
                Dear HR Manager,<br><br>
                The {} has been submitted for your review and approval. You can view it <a href="{}">here</a>.<br><br>
                Kind regards,<br>
                {}
            """.format(doc.doctype, doctype_url, employee.employee_name)
            
            send_email(
                recipients=hr_manager_emails,
                subject=frappe._('Work Continuity Plan Submission'),
                message=message,
                pdf_content=pdf_content,
                doc_name=doc.name
            )
            
        elif doc.workflow_state == "Rejected By HR":

            message_to_employee = """
                Dear {},<br><br>
                Your {} has been reviewed and unfortunately, it has been rejected. You can view the details <a href="{}">here</a>.<br><br>
                Kind regards,<br>
                HR Department
            """.format(employee.employee_name, doc.doctype, doctype_url)

            
            send_email(
                recipients=[employee_email],
                subject=frappe._('Your Work Continuity Plan has been Rejected'),
                message=message_to_employee,
                pdf_content=pdf_content,
                doc_name=doc.name
            )   
        elif doc.workflow_state == "Approved By HR":

            message_to_employee = """
                Dear {},<br><br>
                Your {} has been reviewed and, it has been Approved By HR. You can view the details <a href="{}">here</a>.<br><br>
                Kind regards,<br>
                HR Department
            """.format(employee.employee_name, doc.doctype, doctype_url)

            send_email(
                recipients=[employee_email],
                subject=frappe._('Your Work Continuity Plan has been Rejected'),
                message=message_to_employee,
                pdf_content=pdf_content,
                doc_name=doc.name
            )       
         
         
            

            # 
doc_events = {
    "Employee Grievance": {
        "on_update": employee_grievance
    },
    "Travel Request": {
        "on_update": alert_supervisor_travel_request
    },
    "Leave Application":{
        "on_update": alert_supervisor_leave_application
    },
    "Asset Custodianship Requisition":{
        "on_update": alert_supervisor_asset_requisition
    },
    "Work Continuity Plan":{
        "on_update": alert_supervisor_work_continuity_plan_submission
    }
}