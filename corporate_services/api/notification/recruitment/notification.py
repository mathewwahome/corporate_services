import frappe
from frappe.utils import get_fullname, get_url_to_form


@frappe.whitelist()
def send_minimum_requirements_rejection_email(docname, reason=None):
    """
    Sends an auto-rejection email when minimum requirements are not met (Phase 1).
    
    Args:
        docname (str): Name of the Job Applicant document.
        reason (str, optional): Additional reason for rejection.
    
    Returns:
        str: Status message.
    """
    # Fetch the Job Applicant document
    doc = frappe.get_doc("Job Applicant", docname)

    if not doc.email_id:
        frappe.throw(f"No email found for applicant {doc.applicant_name}.")

    # Get the job opening details
    job_opening = frappe.get_doc("Job Opening", doc.job_title) if doc.job_title else None
    role_title = job_opening.job_title if job_opening else doc.job_title
    
    # Get company name
    company_name = frappe.db.get_single_value("Global Defaults", "default_company") or "Our Company"
    
    # Get HR manager/recruiter name for signature
    signature_name = get_fullname(frappe.session.user)

    # Build the email message
    email_message = f"""
    Dear {doc.applicant_name},<br><br>
    
    Thank you for your interest in the role of <strong>{role_title}</strong> at {company_name}.<br><br>
    
    Based on the minimum requirements indicated in your application, we will not be progressing 
    with your application at this time. We encourage you to apply again in future if your 
    experience aligns with the requirements of a role.<br><br>
    
    We appreciate the time you took to apply and wish you the best in your career journey.<br><br>
    
    Kind regards,<br>
    {signature_name}<br>
    Human Resources<br>
    {company_name}
    """

    frappe.sendmail(
        recipients=[doc.email_id],
        subject=f"Application Update - {role_title} at {company_name}",
        message=email_message
    )

    # Update the applicant status
    doc.status = "Rejected"
    doc.add_comment("Comment", f"Minimum requirements rejection email sent to {doc.email_id}")
    doc.save(ignore_permissions=True)

    return "Rejection email sent successfully."


@frappe.whitelist()
def send_post_interview_rejection_email(docname, custom_message=None):
    """
    Sends a rejection email after interview (late-stage rejection).
    
    Args:
        docname (str): Name of the Job Applicant document.
        custom_message (str, optional): Custom message to include in the email.
    
    Returns:
        str: Status message.
    """
    # Fetch the Job Applicant document
    doc = frappe.get_doc("Job Applicant", docname)

    if not doc.email_id:
        frappe.throw(f"No email found for applicant {doc.applicant_name}.")

    # Get the job opening details
    job_opening = frappe.get_doc("Job Opening", doc.job_title) if doc.job_title else None
    role_title = job_opening.job_title if job_opening else doc.job_title
    
    # Get company name
    company_name = frappe.db.get_single_value("Global Defaults", "default_company") or "Our Company"
    
    # Get HR manager/recruiter name for signature
    signature_name = get_fullname(frappe.session.user)

    # Build the email message
    custom_section = ""
    if custom_message:
        custom_section = f"<br>{custom_message}<br>"

    email_message = f"""
    Dear {doc.applicant_name},<br><br>
    
    Thank you for taking the time to interview for the role of <strong>{role_title}</strong> 
    at {company_name}.<br><br>
    
    After careful consideration, we will not be progressing with your application at this time. 
    This decision was difficult given the high quality of candidates.{custom_section}<br>
    
    We appreciate your interest in {company_name} and encourage you to apply for future 
    opportunities.<br><br>
    
    Kind regards,<br>
    {signature_name}<br>
    Human Resources<br>
    {company_name}
    """

    frappe.sendmail(
        recipients=[doc.email_id],
        subject=f"Application Outcome - {role_title} at {company_name}",
        message=email_message
    )

    # Update the applicant status
    doc.status = "Rejected"
    doc.add_comment("Comment", f"Post-interview rejection email sent to {doc.email_id}")
    doc.save(ignore_permissions=True)

    return "Post-interview rejection email sent successfully."


@frappe.whitelist()
def send_interview_invitation_email(docname, interview_date, interview_time, location, additional_details=None):
    """
    Sends an interview invitation email to the candidate.
    
    Args:
        docname (str): Name of the Job Applicant document.
        interview_date (str): Date of the interview.
        interview_time (str): Time of the interview.
        location (str): Location/venue of the interview (or video call link).
        additional_details (str, optional): Any additional instructions.
    
    Returns:
        str: Status message.
    """
    # Fetch the Job Applicant document
    doc = frappe.get_doc("Job Applicant", docname)

    if not doc.email_id:
        frappe.throw(f"No email found for applicant {doc.applicant_name}.")

    # Get the job opening details
    job_opening = frappe.get_doc("Job Opening", doc.job_title) if doc.job_title else None
    role_title = job_opening.job_title if job_opening else doc.job_title
    
    # Get company name
    company_name = frappe.db.get_single_value("Global Defaults", "default_company") or "Our Company"
    
    # Get HR manager/recruiter name for signature
    signature_name = get_fullname(frappe.session.user)

    # Build additional details section
    details_section = ""
    if additional_details:
        details_section = f"<br><strong>Additional Information:</strong><br>{additional_details}<br>"

    # Build the email message
    email_message = f"""
    Dear {doc.applicant_name},<br><br>
    
    We are pleased to invite you for an interview for the role of <strong>{role_title}</strong> 
    at {company_name}.<br><br>
    
    <strong>Interview Details:</strong><br>
    Date: {interview_date}<br>
    Time: {interview_time}<br>
    Location: {location}<br>
    {details_section}<br>
    
    Please confirm your availability by replying to this email. If you have any questions or 
    need to reschedule, please let us know as soon as possible.<br><br>
    
    We look forward to meeting you.<br><br>
    
    Kind regards,<br>
    {signature_name}<br>
    Human Resources<br>
    {company_name}
    """

    frappe.sendmail(
        recipients=[doc.email_id],
        subject=f"Interview Invitation - {role_title} at {company_name}",
        message=email_message
    )

    # Update the applicant status
    doc.status = "Open"
    doc.add_comment("Comment", f"Interview invitation sent to {doc.email_id} for {interview_date} at {interview_time}")
    doc.save(ignore_permissions=True)

    return "Interview invitation email sent successfully."


@frappe.whitelist()
def send_offer_letter_email(docname, position_title, start_date, salary, custom_message=None):
    """
    Sends an offer letter notification email to the candidate.
    
    Args:
        docname (str): Name of the Job Applicant document.
        position_title (str): Official position title.
        start_date (str): Proposed start date.
        salary (str): Salary/compensation details.
        custom_message (str, optional): Additional message or details.
    
    Returns:
        str: Status message.
    """
    # Fetch the Job Applicant document
    doc = frappe.get_doc("Job Applicant", docname)

    if not doc.email_id:
        frappe.throw(f"No email found for applicant {doc.applicant_name}.")

    # Get company name
    company_name = frappe.db.get_single_value("Global Defaults", "default_company") or "Our Company"
    
    # Get HR manager/recruiter name for signature
    signature_name = get_fullname(frappe.session.user)

    # Build custom message section
    custom_section = ""
    if custom_message:
        custom_section = f"<br>{custom_message}<br>"

    # Build the email message
    email_message = f"""
    Dear {doc.applicant_name},<br><br>
    
    We are delighted to offer you the position of <strong>{position_title}</strong> 
    at {company_name}.<br><br>
    
    <strong>Offer Details:</strong><br>
    Position: {position_title}<br>
    Proposed Start Date: {start_date}<br>
    Compensation: {salary}<br>
    {custom_section}<br>
    
    A formal offer letter with complete terms and conditions will be sent to you separately. 
    Please review it carefully and let us know if you have any questions.<br><br>
    
    We are excited about the possibility of you joining our team and look forward to 
    your response.<br><br>
    
    Congratulations!<br><br>
    
    Kind regards,<br>
    {signature_name}<br>
    Human Resources<br>
    {company_name}
    """

    frappe.sendmail(
        recipients=[doc.email_id],
        subject=f"Job Offer - {position_title} at {company_name}",
        message=email_message
    )

    # Update the applicant status
    doc.status = "Accepted"
    doc.add_comment("Comment", f"Offer letter notification sent to {doc.email_id}")
    doc.save(ignore_permissions=True)

    return "Offer letter notification email sent successfully."