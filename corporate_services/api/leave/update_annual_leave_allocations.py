import frappe
from frappe.utils import getdate, add_months, get_first_day, get_last_day
from datetime import timedelta
import traceback

@frappe.whitelist()
def update_annual_leave_allocations():
    try:
        today = getdate()
        # Set date range from January to December of current year
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
        
        # Get current month's first and last day for allocation check
        current_month_start = get_first_day(today)
        current_month_end = get_last_day(today)

        try:
            leave_settings = frappe.get_doc("Leave Allocation Setting")
            leave_type = leave_settings.leave_type
            leave_days = leave_settings.days_to_add
            hr_email = leave_settings.hr_email  # Get HR email from settings
        except Exception as e:
            if not frappe.db.exists("Leave Allocation Setting"):
                raise ValueError("Please create Leave Allocation Setting record first")
            else:
                raise ValueError(f"Error fetching Leave Allocation Setting: {str(e)}")

        if not leave_type or not leave_days:
            raise ValueError("Leave type and days to add must be specified in Leave Allocation Setting")
        
        if not hr_email:
            raise ValueError("HR email must be specified in Leave Allocation Setting")

        employees = frappe.get_all("Employee", fields=["name"])
        if not employees:
            raise ValueError("No active employees found")

        leave_allocation_settings_data = f"""
        <strong>Leave Type:</strong> {leave_type}<br>
        <strong>Days:</strong> {leave_days}<br>
        <strong>Period:</strong> {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}
        """

        allocation_count = 0
        skipped_count = 0
        for employee in employees:
            # Check if employee has been allocated leave this month
            monthly_allocation = frappe.get_all("Leave Allocation", 
                filters={
                    "employee": employee["name"],
                    "leave_type": leave_type,
                    "creation": ["between", [current_month_start, current_month_end]],
                    "docstatus": 1
                })
            
            if monthly_allocation:
                skipped_count += 1
                frappe.log_error(
                    f"Skipped leave allocation for employee {employee['name']} - Already allocated this month",
                    "Leave Allocation Skip Log"
                )
                continue

            # Get annual allocation
            allocation = frappe.get_all("Leave Allocation", 
                filters={
                    "employee": employee["name"],
                    "leave_type": leave_type,
                    "from_date": start_date,
                    "to_date": end_date,
                    "docstatus": 1
                }, 
                fields=["name", "new_leaves_allocated", "total_leaves_allocated"])

            try:
                if allocation:
                    # Update existing allocation
                    allocation_doc = frappe.get_doc("Leave Allocation", allocation[0]["name"])
                    old_new_leaves = allocation_doc.new_leaves_allocated
                    old_total_leaves = allocation_doc.total_leaves_allocated
                    
                    allocation_doc.new_leaves_allocated = old_new_leaves + leave_days
                    allocation_doc.total_leaves_allocated = old_total_leaves + leave_days
                    
                    allocation_doc.db_update()
                    frappe.db.commit()
                    
                    frappe.log_error(
                        f"Updated leave allocation for employee {employee['name']}: "
                        f"New leaves: {old_new_leaves} -> {allocation_doc.new_leaves_allocated}, "
                        f"Total leaves: {old_total_leaves} -> {allocation_doc.total_leaves_allocated}",
                        "Leave Allocation Update Log"
                    )
                else:
                    # Create new allocation
                    leave_allocation = frappe.get_doc({
                        "doctype": "Leave Allocation",
                        "employee": employee["name"],
                        "leave_type": leave_type,
                        "from_date": start_date,
                        "to_date": end_date,
                        "new_leaves_allocated": leave_days,
                        "total_leaves_allocated": leave_days
                    })
                    leave_allocation.insert(ignore_permissions=True)
                    leave_allocation.submit()
                allocation_count += 1
            except Exception as e:
                frappe.log_error(
                    f"Error allocating leave for employee {employee['name']}: {str(e)}", 
                    "Leave Allocation Error"
                )

        # Send success email notification with additional information
        success_message = f"""
        <strong>Successfully updated {allocation_count} employee allocations.</strong><br>
        <strong>Skipped {skipped_count} employees</strong> (already allocated this month).
        """
        
        send_email_notification(
            leave_allocation_settings_data,
            success_message=success_message,
            hr_email=hr_email
        )

        return f"Successfully updated {allocation_count} employee allocations. Skipped {skipped_count} employees."

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()
        
        frappe.log_error(
            f"Error while updating leave allocations: {error_message}\n{error_traceback}", 
            "Leave Allocation Update Error"
        )
        
        send_email_notification(error_message=error_message, error_traceback=error_traceback, hr_email=hr_email)
        
        raise

def send_email_notification(leave_allocation_settings_data=None, success_message=None, 
                          error_message=None, error_traceback=None, hr_email=None):
    """Function to send email notifications with improved HTML formatting"""
    if error_message:
        subject = "Error in Leave Allocation Update"
        message = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Leave Allocation Update Error</h2>
            
            <p>Hello,</p>
            
            <p>An error occurred while updating the annual leave allocations:</p>
            
            <div style="background-color: #fff3f3; padding: 15px; border-left: 4px solid #ff0000; margin: 10px 0;">
                <strong>Error Message:</strong><br>
                {error_message}
            </div>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #666; margin: 10px 0;">
                <strong>Traceback:</strong><br>
                <pre style="white-space: pre-wrap;">{error_traceback}</pre>
            </div>
            
            <p>Best regards,<br>Your HR System</p>
        </div>
        """
    else:
        subject = "Leave Allocation Update"
        message = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Leave Allocation Update Summary</h2>
            
            <p>Hello,</p>
            
            <div style="background-color: #f0f7ff; padding: 15px; border-left: 4px solid #0066cc; margin: 10px 0;">
                {success_message}
            </div>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #666; margin: 10px 0;">
                <strong>Leave Allocation Settings:</strong><br>
                {leave_allocation_settings_data}
            </div>
            
            <p>Best regards,<br>Your HR System</p>
        </div>
        """

    frappe.sendmail(
        recipients=hr_email,
        subject=subject,
        message=message
    )