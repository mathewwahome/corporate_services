import frappe
from frappe.utils import get_fullname

@frappe.whitelist()
def send_bulk_rejection_emails(job_opening_name, selected_candidate_name=None):
    """
    Automatically sends rejection emails to all remaining candidates when a candidate is selected.
    The email template varies based on the stage the candidate reached:
    - Early stage (Applied/Screening): Minimum requirements not met template
    - Late stage (Interview/Hold): Post-interview rejection template
    
    Args:
        job_opening_name (str): Name of the Job Opening document.
        selected_candidate_name (str, optional): Name of the selected candidate to exclude from rejections.
    
    Returns:
        dict: Summary of emails sent.
    """
    # Fetch all applicants for this job opening
    applicants = frappe.get_all(
        "Job Applicant",
        filters={
            "job_title": job_opening_name,
            "status": ["not in", ["Rejected", "Accepted"]]
        },
        fields=["name", "applicant_name", "email_id", "status"]
    )
    
    if not applicants:
        return {
            "success": True,
            "message": "No pending applicants to reject.",
            "early_stage_count": 0,
            "late_stage_count": 0
        }
    
    # Exclude the selected candidate if provided
    if selected_candidate_name:
        applicants = [app for app in applicants if app.name != selected_candidate_name]
    
    early_stage_count = 0
    late_stage_count = 0
    failed_emails = []
    
    # Process each applicant
    for applicant in applicants:
        try:
            # Determine stage based on status
            stage = determine_rejection_stage(applicant.status)
            
            if stage == "early":
                send_early_stage_rejection(applicant, job_opening_name)
                early_stage_count += 1
            else:  # late stage
                send_late_stage_rejection(applicant, job_opening_name)
                late_stage_count += 1
                
        except Exception as e:
            failed_emails.append({
                "applicant": applicant.name,
                "error": str(e)
            })
            frappe.log_error(
                message=f"Failed to send rejection email to {applicant.email_id}: {str(e)}",
                title=f"Rejection Email Failed - {applicant.name}"
            )
    
    # Return summary
    return {
        "success": True,
        "message": f"Rejection emails sent successfully. Early stage: {early_stage_count}, Late stage: {late_stage_count}",
        "early_stage_count": early_stage_count,
        "late_stage_count": late_stage_count,
        "failed_count": len(failed_emails),
        "failed_emails": failed_emails
    }


def determine_rejection_stage(applicant_status):
    """
    Determines whether the applicant is at early or late stage based on their status.
    
    Args:
        applicant_status (str): Current status of the applicant.
    
    Returns:
        str: "early" or "late"
    """
    # Early stage statuses
    early_stage_statuses = [
        "Open",
        "Applied",
        "In Review",
        "Screening"
    ]
    
    # Late stage statuses (interviewed or advanced)
    late_stage_statuses = [
        "Interview Scheduled",
        "Interviewed",
        "Hold",
        "Replied"
    ]
    
    if applicant_status in early_stage_statuses:
        return "early"
    elif applicant_status in late_stage_statuses:
        return "late"
    else:
        # Default to early stage for unknown statuses
        return "early"


def send_early_stage_rejection(applicant, job_opening_name):
    """
    Sends minimum requirements rejection email (early stage).
    
    Args:
        applicant (dict): Applicant details.
        job_opening_name (str): Name of the Job Opening.
    """
    if not applicant.email_id:
        frappe.throw(f"No email found for applicant {applicant.applicant_name}.")
    
    # Get job opening details
    job_opening = frappe.get_doc("Job Opening", job_opening_name)
    role_title = job_opening.job_title
    
    # Get company name
    company_name = job_opening.company or frappe.db.get_single_value("Global Defaults", "default_company") or "Our Company"
    
    # Get HR manager/recruiter name for signature
    signature_name = get_fullname(frappe.session.user)
    
    # Build the email message
    email_message = f"""
    Dear {applicant.applicant_name},<br><br>
    
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
        recipients=[applicant.email_id],
        subject=f"Application Update - {role_title} at {company_name}",
        message=email_message
    )
    
    # Update the applicant status
    doc = frappe.get_doc("Job Applicant", applicant.name)
    doc.status = "Rejected"
    doc.add_comment("Comment", f"Early stage rejection email sent (auto-triggered)")
    doc.save(ignore_permissions=True)


def send_late_stage_rejection(applicant, job_opening_name):
    """
    Sends post-interview rejection email (late stage).
    
    Args:
        applicant (dict): Applicant details.
        job_opening_name (str): Name of the Job Opening.
    """
    if not applicant.email_id:
        frappe.throw(f"No email found for applicant {applicant.applicant_name}.")
    
    # Get job opening details
    job_opening = frappe.get_doc("Job Opening", job_opening_name)
    role_title = job_opening.job_title
    
    # Get company name
    company_name = job_opening.company or frappe.db.get_single_value("Global Defaults", "default_company") or "Our Company"
    
    # Get HR manager/recruiter name for signature
    signature_name = get_fullname(frappe.session.user)
    
    # Build the email message
    email_message = f"""
    Dear {applicant.applicant_name},<br><br>
    
    Thank you for taking the time to interview for the role of <strong>{role_title}</strong> 
    at {company_name}.<br><br>
    
    After careful consideration, we will not be progressing with your application at this time. 
    This decision was difficult given the high quality of candidates.<br><br>
    
    We appreciate your interest in {company_name} and encourage you to apply for future 
    opportunities.<br><br>
    
    Kind regards,<br>
    {signature_name}<br>
    Human Resources<br>
    {company_name}
    """
    
    frappe.sendmail(
        recipients=[applicant.email_id],
        subject=f"Application Outcome - {role_title} at {company_name}",
        message=email_message
    )
    
    # Update the applicant status
    doc = frappe.get_doc("Job Applicant", applicant.name)
    doc.status = "Rejected"
    doc.add_comment("Comment", f"Late stage rejection email sent (auto-triggered)")
    doc.save(ignore_permissions=True)


@frappe.whitelist()
def send_rejection_by_stage(job_opening_name, stage_filter="all", exclude_candidates=None):
    """
    Sends rejection emails to candidates filtered by specific stage.
    
    Args:
        job_opening_name (str): Name of the Job Opening document.
        stage_filter (str): "early", "late", or "all" (default: "all").
        exclude_candidates (list, optional): List of candidate names to exclude.
    
    Returns:
        dict: Summary of emails sent.
    """
    # Fetch all applicants for this job opening
    applicants = frappe.get_all(
        "Job Applicant",
        filters={
            "job_title": job_opening_name,
            "status": ["not in", ["Rejected", "Accepted"]]
        },
        fields=["name", "applicant_name", "email_id", "status"]
    )
    
    if not applicants:
        return {
            "success": True,
            "message": "No pending applicants to reject.",
            "count": 0
        }
    
    # Exclude specified candidates
    if exclude_candidates:
        if isinstance(exclude_candidates, str):
            exclude_candidates = [exclude_candidates]
        applicants = [app for app in applicants if app.name not in exclude_candidates]
    
    sent_count = 0
    failed_emails = []
    
    # Process each applicant
    for applicant in applicants:
        try:
            # Determine stage
            stage = determine_rejection_stage(applicant.status)
            
            # Apply stage filter
            if stage_filter != "all" and stage != stage_filter:
                continue
            
            # Send appropriate rejection email
            if stage == "early":
                send_early_stage_rejection(applicant, job_opening_name)
            else:
                send_late_stage_rejection(applicant, job_opening_name)
            
            sent_count += 1
            
        except Exception as e:
            failed_emails.append({
                "applicant": applicant.name,
                "error": str(e)
            })
            frappe.log_error(
                message=f"Failed to send rejection email to {applicant.email_id}: {str(e)}",
                title=f"Rejection Email Failed - {applicant.name}"
            )
    
    # Return summary
    return {
        "success": True,
        "message": f"{sent_count} rejection emails sent successfully.",
        "sent_count": sent_count,
        "failed_count": len(failed_emails),
        "failed_emails": failed_emails
    }


@frappe.whitelist()
def preview_rejection_emails(job_opening_name):
    """
    Preview which candidates will receive which rejection template without sending emails.
    
    Args:
        job_opening_name (str): Name of the Job Opening document.
    
    Returns:
        dict: Preview of candidates grouped by rejection stage.
    """
    # Fetch all applicants for this job opening
    applicants = frappe.get_all(
        "Job Applicant",
        filters={
            "job_title": job_opening_name,
            "status": ["not in", ["Rejected", "Accepted"]]
        },
        fields=["name", "applicant_name", "email_id", "status"]
    )
    
    early_stage = []
    late_stage = []
    
    for applicant in applicants:
        stage = determine_rejection_stage(applicant.status)
        
        candidate_info = {
            "name": applicant.name,
            "applicant_name": applicant.applicant_name,
            "email": applicant.email_id,
            "status": applicant.status
        }
        
        if stage == "early":
            early_stage.append(candidate_info)
        else:
            late_stage.append(candidate_info)
    
    return {
        "job_opening": job_opening_name,
        "early_stage": {
            "count": len(early_stage),
            "template": "Minimum Requirements Not Met",
            "candidates": early_stage
        },
        "late_stage": {
            "count": len(late_stage),
            "template": "Post-Interview Rejection",
            "candidates": late_stage
        },
        "total": len(applicants)
    }