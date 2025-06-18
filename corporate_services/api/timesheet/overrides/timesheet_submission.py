import frappe
from frappe import _

@frappe.whitelist()
def delete_timesheet_submission_with_linked(timesheet_submission_name):
    """
    Delete timesheet submission and all its linked timesheets
    """
    try:
        if not timesheet_submission_name:
            frappe.throw(_("Timesheet Submission name is required"))
        
        if not frappe.db.exists("Timesheet Submission", timesheet_submission_name):
            frappe.throw(_("Timesheet Submission {0} does not exist").format(timesheet_submission_name))
        
        # Set flag to allow custom deletion
        frappe.local.flags.custom_delete_in_progress = True
        frappe.local.flags.ignore_links = True
        frappe.local.flags.ignore_submit_comment = True
        
        frappe.db.begin()
        
        ts_submission = frappe.get_doc("Timesheet Submission", timesheet_submission_name)
        
        ts_submission.check_permission("delete")
        
        # Get all linked timesheets from the child table
        linked_timesheets = frappe.get_all(
            "Timesheet Submission List", 
            filters={"parent": timesheet_submission_name},
            fields=["timesheet"]
        )
        
        deleted_count = 0
        failed_deletions = []
        
        # Remove the links from the timesheet submission to avoid validation errors
        for timesheet_row in linked_timesheets:
            try:
                timesheet_name = timesheet_row.timesheet
                if frappe.db.exists("Timesheet", timesheet_name):
                    # Remove the reference from timesheet to timesheet submission
                    frappe.db.set_value("Timesheet", timesheet_name, "custom_timesheet_submission", None)
                    frappe.db.set_value("Timesheet", timesheet_name, "custom_timesheet_submission_name", None)
                    
            except Exception as e:
                frappe.log_error(f"Error removing link for timesheet {timesheet_name}: {str(e)}", "Link Removal Error")
                continue
        
        frappe.db.delete("Timesheet Submission List", {"parent": timesheet_submission_name})
        
        # Delete all linked timesheets
        for timesheet_row in linked_timesheets:
            try:
                timesheet_name = timesheet_row.timesheet
                if frappe.db.exists("Timesheet", timesheet_name):
                    timesheet_doc = frappe.get_doc("Timesheet", timesheet_name)
                    
                    timesheet_doc.check_permission("delete")
                    
                    # Set flags to bypass validations
                    timesheet_doc.flags.ignore_validate = True
                    timesheet_doc.flags.ignore_mandatory = True
                    timesheet_doc.flags.ignore_links = True
                    timesheet_doc.flags.ignore_submit_comment = True
                    
                    # Check if timesheet is submitted - if so, cancel first
                    if timesheet_doc.docstatus == 1:
                        timesheet_doc.flags.ignore_validate_on_cancel = True
                        timesheet_doc.cancel()
                    
                    # Delete the timesheet
                    frappe.delete_doc("Timesheet", timesheet_name, force=True, ignore_permissions=False)
                    deleted_count += 1
                    
            except Exception as e:
                error_msg = f"Error deleting timesheet {timesheet_name}: {str(e)}"
                frappe.log_error(error_msg, "Timesheet Deletion Error")
                failed_deletions.append(timesheet_name)
                continue
        
        # Check if timesheet submission is submitted - if so, cancel first
        if ts_submission.docstatus == 1:
            ts_submission.flags.ignore_validate_on_cancel = True
            ts_submission.cancel()
        
        # Set flags for timesheet submission deletion
        ts_submission.flags.ignore_validate = True
        ts_submission.flags.ignore_links = True
        
        # Now delete the timesheet submission
        frappe.delete_doc("Timesheet Submission", timesheet_submission_name, force=True, ignore_permissions=False)
        
        frappe.db.commit()
        
        frappe.local.flags.custom_delete_in_progress = False
        frappe.local.flags.ignore_links = False
        frappe.local.flags.ignore_submit_comment = False
        
        message = f"Successfully deleted Timesheet Submission {timesheet_submission_name} and {deleted_count} linked timesheets"
        if failed_deletions:
            message += f". Failed to delete {len(failed_deletions)} timesheets: {', '.join(failed_deletions)}"
        
        return {
            "success": True,
            "message": message,
            "deleted_timesheets": deleted_count,
            "failed_deletions": failed_deletions
        }
        
    except Exception as e:
        frappe.db.rollback()
        
        frappe.local.flags.custom_delete_in_progress = False
        frappe.local.flags.ignore_links = False
        frappe.local.flags.ignore_submit_comment = False
        
        error_msg = f"Error in delete_timesheet_submission_with_linked: {str(e)}"
        frappe.log_error(error_msg, "Timesheet Submission Deletion Error")
        
        return {
            "success": False,
            "message": str(e),
            "error": True
        }

@frappe.whitelist()
def force_delete_timesheet_with_links(timesheet_name):
    """
    Force delete a timesheet even if it has links
    """
    try:
        if not frappe.db.exists("Timesheet", timesheet_name):
            return {"success": False, "message": f"Timesheet {timesheet_name} does not exist"}
        
        frappe.local.flags.ignore_links = True
        frappe.local.flags.ignore_submit_comment = True
        
        # Remove any references to this timesheet
        frappe.db.delete("Timesheet Submission List", {"timesheet": timesheet_name})
        
        # Get and delete the timesheet
        timesheet_doc = frappe.get_doc("Timesheet", timesheet_name)
        
        if timesheet_doc.docstatus == 1:
            timesheet_doc.flags.ignore_validate_on_cancel = True
            timesheet_doc.cancel()
        
        timesheet_doc.flags.ignore_validate = True
        timesheet_doc.flags.ignore_links = True
        
        frappe.delete_doc("Timesheet", timesheet_name, force=True)
        
        frappe.local.flags.ignore_links = False
        frappe.local.flags.ignore_submit_comment = False
        
        return {"success": True, "message": f"Successfully deleted timesheet {timesheet_name}"}
        
    except Exception as e:
        frappe.local.flags.ignore_links = False
        frappe.local.flags.ignore_submit_comment = False
        frappe.log_error(f"Error force deleting timesheet {timesheet_name}: {str(e)}", "Force Delete Error")
        return {"success": False, "message": str(e)}

def prevent_default_delete(doc, method):
    """
    Prevent default delete behavior for Timesheet Submission
    """
    if frappe.local.flags.get('custom_delete_in_progress') or frappe.local.flags.get('ignore_links'):
        return
    
    linked_count = frappe.db.count("Timesheet Submission List", {"parent": doc.name})
    
    if linked_count > 0:
        frappe.throw(
            _("Cannot delete Timesheet Submission {0} as it has {1} linked timesheet(s). Use the custom delete option instead.").format(
                doc.name, linked_count
            )
        )

def prevent_timesheet_delete_if_linked(doc, method):
    """
    Prevent timesheet deletion if linked to submission (unless forced)
    """
    if (frappe.local.flags.get('custom_delete_in_progress') or 
        frappe.local.flags.get('ignore_links')):
        return
    
    linked_submissions = frappe.get_all(
        "Timesheet Submission List",
        filters={"timesheet": doc.name},
        fields=["parent"]
    )
    
    if linked_submissions:
        submission_names = [sub.parent for sub in linked_submissions]
        frappe.throw(
            _("Cannot delete Timesheet {0} as it is linked to Timesheet Submission(s): {1}").format(
                doc.name, ", ".join(submission_names)
            )
        )