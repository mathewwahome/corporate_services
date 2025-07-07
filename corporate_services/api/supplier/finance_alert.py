import frappe
from frappe.utils import get_url_to_form
from frappe import _

def send_email(recipients, subject, message, pdf_content=None, doc_name=None):
    attachments = []
    if pdf_content and doc_name:
        attachments = [{
            'fname': '{}.pdf'.format(doc_name),
            'fcontent': pdf_content
        }]
    
    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        attachments=attachments,
        header=("Supplier Quote Notification", "text/html")
    )

def generate_message(doc, email_type, employee_name=None, supplier_name=None):
    doctype_url = get_url_to_form(doc.doctype, doc.name)
    
    messages = {
        # Supplier notifications
        "quote_received": """
            Dear {},<br><br>
            Thank you for submitting your quotation for <strong>{}</strong>.<br><br>
            We have successfully received your quote and it is currently under review by our procurement team. 
            We will get back to you with our decision within the next few business days.<br><br>
            Reference Number: <strong>{}</strong><br><br>
            Thank you for your interest in working with us.<br><br>
            Best regards,<br>
            Procurement Team
        """.format(supplier_name or "Valued Supplier", doc.get("title") or "your quotation", doc.name),
        
        "quote_approved": """
            Dear {},<br><br>
            Congratulations! We are pleased to inform you that your quotation for <strong>{}</strong> has been approved.<br><br>
            Reference Number: <strong>{}</strong><br><br>
            Our procurement team will contact you shortly to discuss the next steps and finalize the terms.<br><br>
            Thank you for your competitive proposal.<br><br>
            Best regards,<br>
            Procurement Team
        """.format(supplier_name or "Valued Supplier", doc.get("title") or "your quotation", doc.name),
        
        "quote_rejected": """
            Dear {},<br><br>
            Thank you for submitting your quotation in response to our recent Request for Quotation <strong>{}</strong>.<br><br>
            After careful consideration, we regret to inform you that we will not be proceeding with your quotation. 
            This decision was primarily based on competitive pricing received from other vendors.
            Reference Number: <strong>{}</strong><br><br>
            We appreciate your effort and welcome future collaboration opportunities.<br><br>
            Kind regards,<br>
            Procurement Team
        """.format(supplier_name or "Valued Supplier", doc.get("title") or "your quotation", doc.name),
        
        # Internal notifications
        "employee_notification": """
            Dear {},<br><br>
            A new supplier quotation has been submitted for review.<br><br>
            Quotation Details:<br>
            - Reference: <strong>{}</strong><br>
            - Supplier: <strong>{}</strong><br>
            - Status: Pending Review<br><br>
            You can view the quotation <a href="{}">here</a>.<br><br>
            Please review and take appropriate action.<br><br>
            Best regards,<br>
            System Notification
        """.format(employee_name, doc.name, supplier_name or "N/A", doctype_url)
    }
    
    return messages.get(email_type, "")

def get_supplier_email(doc):
    """Get supplier email from the document"""
    supplier_email = None
    
    # Try to get supplier email from various possible fields
    if hasattr(doc, 'supplier_email') and doc.supplier_email:
        supplier_email = doc.supplier_email
    elif hasattr(doc, 'supplier') and doc.supplier:
        # Get supplier email from Supplier master
        supplier_doc = frappe.get_doc("Supplier", doc.supplier)
        supplier_email = supplier_doc.email_id
    elif hasattr(doc, 'email') and doc.email:
        supplier_email = doc.email
    
    return supplier_email

def get_supplier_name(doc):
    """Get supplier name from the document"""
    supplier_name = None
    
    if hasattr(doc, 'supplier_name') and doc.supplier_name:
        supplier_name = doc.supplier_name
    elif hasattr(doc, 'supplier') and doc.supplier:
        supplier_name = doc.supplier
    elif hasattr(doc, 'company_name') and doc.company_name:
        supplier_name = doc.company_name
    elif hasattr(doc, 'suppliers_name') and doc.suppliers_name:
        supplier_name = doc.suppliers_name
    
    return supplier_name

def alert(doc, method):
    """Main alert function that handles all notifications based on document state"""
    try:
        if method == "on_update":
            handle_workflow_change(doc, method)
        elif method == "after_workflow_action":
            handle_workflow_change(doc, method)
        else:
            if doc.is_new():
                notify_on_submission(doc, method)
            else:
                handle_workflow_change(doc, method)
                
    except Exception as e:
        frappe.log_error(
            message=f"Error in supplier notification alert: {str(e)}",
            title="Supplier Quote Notification Error"
        )

def notify_on_submission(doc, method):
    """Send notification when supplier submits quotation"""
    supplier_email = get_supplier_email(doc)
    supplier_name = get_supplier_name(doc)
    
    if supplier_email:
        message = generate_message(doc, "quote_received", supplier_name=supplier_name)
        send_email(
            recipients=[supplier_email],
            subject=frappe._('Quotation Received - Reference: {}').format(doc.name),
            message=message
        )
    
    # Notify internal team
    procurement_managers = frappe.get_all('Has Role', 
                                        filters={'role': 'Purchase Manager'}, 
                                        fields=['parent'])
    if procurement_managers:
        manager_emails = [frappe.get_value('User', manager.parent, 'email') 
                         for manager in procurement_managers if frappe.get_value('User', manager.parent, 'email')]
        
        if manager_emails:
            internal_message = generate_message(doc, "employee_notification", 
                                              employee_name="Purchase Manager",
                                              supplier_name=supplier_name)
            send_email(
                recipients=manager_emails,
                subject=frappe._('New Supplier Quotation Submitted - {}').format(doc.name),
                message=internal_message
            )

def notify_on_approval(doc, method):
    """Send notification when quotation is approved"""
    # Check if status changed to approved
    if hasattr(doc, 'workflow_state') and doc.workflow_state == 'Approved':
        supplier_email = get_supplier_email(doc)
        supplier_name = get_supplier_name(doc)
        
        if supplier_email:
            print_format = "Standard"
            pdf_content = frappe.get_print(doc.doctype, doc.name, print_format, as_pdf=True)
            
            message = generate_message(doc, "quote_approved", supplier_name=supplier_name)
            send_email(
                recipients=[supplier_email],
                subject=frappe._('Quotation Approved - Reference: {}').format(doc.name),
                message=message,
                pdf_content=pdf_content,
                doc_name=doc.name
            )

def notify_on_rejection(doc, method):
    """Send notification when quotation is rejected"""
    # Check if status changed to rejected
    if hasattr(doc, 'workflow_state') and doc.workflow_state == 'Rejected':
        supplier_email = get_supplier_email(doc)
        supplier_name = get_supplier_name(doc)
        
        if supplier_email:
            message = generate_message(doc, "quote_rejected", supplier_name=supplier_name)
            send_email(
                recipients=[supplier_email],
                subject=frappe._('Quotation Status Update - Reference: {}').format(doc.name),
                message=message
            )








# WORKFLOW HANDLERS
def handle_workflow_change(doc, method):
    """Handle workflow state changes"""
    if hasattr(doc, 'workflow_state'):
        if doc.workflow_state == 'Approved':
            notify_on_approval(doc, method)
        elif doc.workflow_state == 'Submitted':
            notify_on_submission(doc, method)
        elif doc.workflow_state == 'Rejected':
            notify_on_rejection(doc, method)

# Document Events Configuration
doc_events = {
    "Supplier Quote Submission": {
        "on_submit": notify_on_submission,
        "on_update": handle_workflow_change,
        "after_workflow_action": handle_workflow_change
    }
}