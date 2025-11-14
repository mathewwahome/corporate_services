import frappe
from frappe import _
import json
import re

# Constants
DOCTYPE_JOB_CANDIDATE = 'Job Candidate'


@frappe.whitelist()
def create_job_candidate():
    """
    Create a Job Candidate entry from external system.
    Accepts multipart/form-data with files and JSON data.
    
    Required fields:
    - names: Candidate's full name
    - email_address: Valid email address
    - cv: Resume/CV file (attached)
    
    Optional fields:
    - phone: Phone number
    - role: Role/position name the candidate is applying for
    - role_description: Description of the role
    - cover_letter: Cover letter file (attached)
    - minimum_requirements: JSON array of minimum requirements
    - preferred_attributes: JSON array of preferred attributes
    
    Returns:
    - Success: {"success": true, "data": {candidate details}}
    - Error: {"success": false, "errors": {field: error_message}}
    """
    try:
        # Parse form data
        form_data = frappe.local.form_dict
        files = frappe.request.files
        
        # Validate and extract form fields
        validation_errors = {}
        
        # Extract and validate required fields
        names = form_data.get('names', '').strip()
        email_address = form_data.get('email_address', '').strip()
        phone = form_data.get('phone', '').strip()
        role = form_data.get('role', '').strip()
        role_description = form_data.get('role_description', '').strip()
        
        # Validate names
        if not names:
            validation_errors['names'] = 'Candidate name is required'
        
        # Validate email
        if not email_address:
            validation_errors['email_address'] = 'Email address is required'
        elif not is_valid_email(email_address):
            validation_errors['email_address'] = 'Invalid email address format'
        
        # Validate CV file
        cv_file = files.get('cv')
        if not cv_file:
            validation_errors['cv'] = 'Resume/CV file is required'
        
        # Get optional cover letter file
        cover_letter_file = files.get('cover_letter')
        
        # Parse child table data
        minimum_requirements = []
        preferred_attributes = []
        
        if form_data.get('minimum_requirements'):
            try:
                minimum_requirements = json.loads(form_data.get('minimum_requirements'))
                if not isinstance(minimum_requirements, list):
                    validation_errors['minimum_requirements'] = 'Minimum requirements must be an array'
            except json.JSONDecodeError:
                validation_errors['minimum_requirements'] = 'Invalid JSON format for minimum requirements'
        
        if form_data.get('preferred_attributes'):
            try:
                preferred_attributes = json.loads(form_data.get('preferred_attributes'))
                if not isinstance(preferred_attributes, list):
                    validation_errors['preferred_attributes'] = 'Preferred attributes must be an array'
            except json.JSONDecodeError:
                validation_errors['preferred_attributes'] = 'Invalid JSON format for preferred attributes'
        
        # Return validation errors if any
        if validation_errors:
            return {
                'success': False,
                'errors': validation_errors
            }
        
        # Create the Job Candidate document
        candidate_doc = frappe.get_doc({
            'doctype': DOCTYPE_JOB_CANDIDATE,
            'names': names,
            'email_address': email_address,
            'phone': phone if phone else None,
            'role': role if role else None,
            'role_description': role_description if role_description else None
        })
        
        # Save CV file
        if cv_file:
            cv_file_doc = save_file(
                file=cv_file,
                doctype=DOCTYPE_JOB_CANDIDATE,
                docname=None,  # Will be updated after insert
                fieldname='cv'
            )
            candidate_doc.cv = cv_file_doc.file_url
        
        # Save cover letter file if provided
        if cover_letter_file:
            cover_letter_doc = save_file(
                file=cover_letter_file,
                doctype=DOCTYPE_JOB_CANDIDATE,
                docname=None,
                fieldname='cover_letter'
            )
            candidate_doc.cover_letter = cover_letter_doc.file_url
        
        # Add minimum requirements child table entries
        for req in minimum_requirements:
            if isinstance(req, dict):
                candidate_doc.append('minimum_requirements', req)
        
        # Add preferred attributes child table entries
        for attr in preferred_attributes:
            if isinstance(attr, dict):
                candidate_doc.append('preferred_attributes', attr)
        
        # Insert the document
        candidate_doc.insert(ignore_permissions=True)
        
        # Update file attachments to link to the created document
        if cv_file:
            update_file_attachment(cv_file_doc.name, candidate_doc.name, DOCTYPE_JOB_CANDIDATE, 'cv')
        if cover_letter_file:
            update_file_attachment(cover_letter_doc.name, candidate_doc.name, DOCTYPE_JOB_CANDIDATE, 'cover_letter')
        
        # Commit the transaction
        frappe.db.commit()
        
        # Return success response
        return {
            'success': True,
            'data': {
                'name': candidate_doc.name,
                'names': candidate_doc.names,
                'email_address': candidate_doc.email_address,
                'phone': candidate_doc.phone,
                'role': candidate_doc.role,
                'role_description': candidate_doc.role_description,
                'cv': candidate_doc.cv,
                'cover_letter': candidate_doc.cover_letter
            }
        }
        
    except frappe.DuplicateEntryError:
        frappe.db.rollback()
        return {
            'success': False,
            'errors': {
                'email_address': 'A candidate with this email already exists'
            }
        }
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), 'Job Candidate API Error')
        return {
            'success': False,
            'errors': {
                'general': str(e)
            }
        }


def is_valid_email(email):
    """Validate email address format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None


def save_file(file, doctype, docname, fieldname):
    """
    Save uploaded file to ERPNext File doctype
    
    Args:
        file: FileStorage object from request
        doctype: DocType to attach file to
        docname: Document name to attach file to (can be None initially)
        fieldname: Field name where file is attached
    
    Returns:
        File document
    """
    file_data = {
        'doctype': 'File',
        'file_name': file.filename,
        'is_private': 1,
        'content': file.read()
    }
    
    # Only set attachment fields if docname is provided
    # Frappe requires both attached_to_doctype and attached_to_name together
    if docname:
        file_data['attached_to_doctype'] = doctype
        file_data['attached_to_name'] = docname
        file_data['attached_to_field'] = fieldname
    
    file_doc = frappe.get_doc(file_data)
    file_doc.save(ignore_permissions=True)
    return file_doc


def update_file_attachment(file_name, docname, doctype, fieldname):
    """
    Update file attachment to link to the created document
    
    Args:
        file_name: Name of the File document
        docname: Name of the Job Candidate document
        doctype: DocType to attach file to
        fieldname: Field name where file is attached
    """
    frappe.db.set_value('File', file_name, {
        'attached_to_doctype': doctype,
        'attached_to_name': docname,
        'attached_to_field': fieldname
    })

