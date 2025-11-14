import frappe
from frappe.utils import getdate, add_months, get_first_day, get_last_day
from datetime import timedelta
import traceback

def get_eligible_employees():
    """
    Get employees who are eligible for leave allocation based on contract type
    Returns list of employees whose contract type has accumulate_monthly_leave checked
    """
    contract_types_with_leave = frappe.get_all("Contract Type", 
        filters={"accumulate_monthly_leave": 1}, 
        fields=["name", "contract_type"])

    if not contract_types_with_leave:
        return [], []

    eligible_contract_types = [ct["contract_type"] for ct in contract_types_with_leave]

    # Get ALL active employees
    all_active_employees = frappe.get_all("Employee", 
        filters={"status": "Active"}, 
        fields=["name", "employee_name", "custom_contract_type"])
    
    eligible_employees = []
    for employee in all_active_employees:
        contract_type = employee.get("custom_contract_type")
        
        # Only include if contract type is in eligible list and not empty
        if contract_type and contract_type.strip() in eligible_contract_types:
            eligible_employees.append(employee)

    return eligible_employees, eligible_contract_types



@frappe.whitelist()
def process_leave_allocations():
    """
    Smart function to handle both new year allocations and monthly updates.
    Automatically detects if new year allocations are needed.
    """
    try:
        today = getdate()
        current_year = today.year
        is_january = today.month == 1
        
        # Get leave settings
        try:
            leave_settings = frappe.get_doc("Leave Allocation Setting")
            leave_type = leave_settings.leave_type
            leave_days = leave_settings.days_to_add
            hr_email = leave_settings.hr_email
        except Exception as e:
            if not frappe.db.exists("Leave Allocation Setting"):
                raise ValueError("Please create Leave Allocation Setting record first")
            else:
                raise ValueError(f"Error fetching Leave Allocation Setting: {str(e)}")

        if not leave_type or not leave_days:
            raise ValueError("Leave type and days to add must be specified in Leave Allocation Setting")
        
        if not hr_email:
            raise ValueError("HR email must be specified in Leave Allocation Setting")

        # Get eligible employees based on contract type
        employees, contract_types_with_leave = get_eligible_employees()

        if not employees:
            if not contract_types_with_leave:
                raise ValueError("No contract types found with 'accumulate_monthly_leave' checked")
            else:
                raise ValueError(f"No active employees found with contract types: {', '.join(contract_types_with_leave)}")

        frappe.log_error(
            f"Found {len(employees)} eligible employees with contract types: {', '.join(contract_types_with_leave)}",
            "Leave Allocation Process - Employee Filter"
        )

        # Check if new year allocations are needed
        needs_new_year_allocation = False
        if is_january:
            # Check if any employee has allocation for this year
            sample_allocation = frappe.get_all("Leave Allocation",
                filters={
                    "leave_type": leave_type,
                    "from_date": today.replace(month=1, day=1),
                    "to_date": today.replace(month=12, day=31),
                    "docstatus": 1
                },
                limit=1
            )
            needs_new_year_allocation = not bool(sample_allocation)

        if needs_new_year_allocation:
            frappe.log_error(
                "Detected start of new year - creating new allocations",
                "Leave Allocation Process"
            )
            return create_new_year_leave_allocations()
        else:
            return update_annual_leave_allocations()

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()
        
        frappe.log_error(
            f"Error in leave allocation process: {error_message}\n{error_traceback}", 
            "Leave Allocation Process Error"
        )
        
        # Try to get hr_email for error notification
        try:
            hr_email = frappe.get_doc("Leave Allocation Setting").hr_email
        except:
            hr_email = None
            
        if hr_email:
            send_email_notification(
                error_message=error_message, 
                error_traceback=error_traceback, 
                hr_email=hr_email
            )
        
        raise
    
@frappe.whitelist()
def update_annual_leave_allocations():
    """Update existing leave allocations or create new ones for the current month"""
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
            hr_email = leave_settings.hr_email
        except Exception as e:
            if not frappe.db.exists("Leave Allocation Setting"):
                raise ValueError("Please create Leave Allocation Setting record first")
            else:
                raise ValueError(f"Error fetching Leave Allocation Setting: {str(e)}")

        if not leave_type or not leave_days:
            raise ValueError("Leave type and days to add must be specified in Leave Allocation Setting")
        
        if not hr_email:
            raise ValueError("HR email must be specified in Leave Allocation Setting")

        # Get eligible employees based on contract type (CORRECTED)
        employees, contract_types_with_leave = get_eligible_employees()
            
        if not employees:
            if not contract_types_with_leave:
                raise ValueError("No contract types found with 'accumulate_monthly_leave' checked")
            else:
                raise ValueError(f"No active employees found with contract types: {', '.join(contract_types_with_leave)}")

        leave_allocation_settings_data = f"""
        <strong>Leave Type:</strong> {leave_type}<br>
        <strong>Days:</strong> {leave_days}<br>
        <strong>Period:</strong> {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}<br>
        <strong>Eligible Contract Types:</strong> {', '.join(contract_types_with_leave)}<br>
        <strong>Eligible Employees:</strong> {len(employees)}
        """

        allocation_count = 0
        update_count = 0
        skipped_count = 0
        error_count = 0
        error_details = []

        for employee in employees:
            try:
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
                        f"Skipped leave allocation for employee {employee['employee_name']} ({employee['custom_contract_type']}) - Already allocated this month",
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

                if allocation:
                    # Update existing allocation
                    allocation_doc = frappe.get_doc("Leave Allocation", allocation[0]["name"])
                    old_new_leaves = allocation_doc.new_leaves_allocated
                    old_total_leaves = allocation_doc.total_leaves_allocated
                    
                    allocation_doc.new_leaves_allocated = old_new_leaves + leave_days
                    allocation_doc.total_leaves_allocated = old_total_leaves + leave_days
                    
                    allocation_doc.db_update()
                    frappe.db.commit()
                    update_count += 1
                    
                    frappe.log_error(
                        f"Updated leave allocation for employee {employee['employee_name']} ({employee['custom_contract_type']}): "
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
                    
                    frappe.log_error(
                        f"Created new leave allocation for employee {employee['employee_name']} ({employee['custom_contract_type']}): "
                        f"Days allocated: {leave_days}",
                        "Leave Allocation Create Log"
                    )

            except Exception as e:
                error_count += 1
                error_details.append(f"Error for {employee['employee_name']} ({employee.get('custom_contract_type', 'N/A')}): {str(e)}")
                frappe.log_error(
                    f"Error processing leave for employee {employee['name']}: {str(e)}", 
                    "Leave Allocation Error"
                )

        # Prepare detailed success message
        success_message = f"""
        <strong>Leave Allocation Update Summary:</strong><br>
        - New allocations created: {allocation_count} employees<br>
        - Existing allocations updated: {update_count} employees<br>
        - Skipped (already allocated this month): {skipped_count} employees<br>
        - Failed: {error_count} employees
        """

        if error_details:
            error_details_html = "<br>".join(error_details)
            success_message += f"<br><br><strong>Error Details:</strong><br>{error_details_html}"

        # Send success email notification
        send_email_notification(
            leave_allocation_settings_data,
            success_message=success_message,
            hr_email=hr_email
        )

        return {
            "message": f"Created {allocation_count}, updated {update_count}, skipped {skipped_count}, failed {error_count}",
            "created": allocation_count,
            "updated": update_count,
            "skipped": skipped_count,
            "failed": error_count,
            "eligible_contract_types": contract_types_with_leave,
            "total_eligible_employees": len(employees)
        }

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()
        
        frappe.log_error(
            f"Error while updating leave allocations: {error_message}\n{error_traceback}", 
            "Leave Allocation Update Error"
        )
        
        # Try to get hr_email for error notification
        try:
            hr_email = frappe.get_doc("Leave Allocation Setting").hr_email
        except:
            hr_email = None
            
        if hr_email:
            send_email_notification(
                error_message=error_message, 
                error_traceback=error_traceback, 
                hr_email=hr_email
            )
        
        raise

@frappe.whitelist()
def create_new_year_leave_allocations():
    """Create new leave allocations for all active employees for the new year"""
    try:
        today = getdate()
        # Set date range for the new year
        new_year = today.year
        start_date = today.replace(year=new_year, month=1, day=1)
        end_date = today.replace(year=new_year, month=12, day=31)

        try:
            leave_settings = frappe.get_doc("Leave Allocation Setting")
            leave_type = leave_settings.leave_type
            leave_days = leave_settings.days_to_add
            hr_email = leave_settings.hr_email
        except Exception as e:
            if not frappe.db.exists("Leave Allocation Setting"):
                raise ValueError("Please create Leave Allocation Setting record first")
            else:
                raise ValueError(f"Error fetching Leave Allocation Setting: {str(e)}")

        if not leave_type or not leave_days:
            raise ValueError("Leave type and days to add must be specified in Leave Allocation Setting")
        
        if not hr_email:
            raise ValueError("HR email must be specified in Leave Allocation Setting")

        # Get eligible employees based on contract type (CORRECTED)
        employees, contract_types_with_leave = get_eligible_employees()
        
        if not employees:
            if not contract_types_with_leave:
                raise ValueError("No contract types found with 'accumulate_monthly_leave' checked")
            else:
                raise ValueError(f"No active employees found with contract types: {', '.join(contract_types_with_leave)}")

        leave_allocation_settings_data = f"""
        <strong>Leave Type:</strong> {leave_type}<br>
        <strong>Annual Days:</strong> {leave_days}<br>
        <strong>Period:</strong> {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}<br>
        <strong>Eligible Contract Types:</strong> {', '.join(contract_types_with_leave)}<br>
        <strong>Eligible Employees:</strong> {len(employees)}
        """

        created_count = 0
        skipped_count = 0
        error_count = 0
        error_details = []

        for employee in employees:
            try:
                # Check if allocation already exists for the new year
                existing_allocation = frappe.get_all("Leave Allocation", 
                    filters={
                        "employee": employee["name"],
                        "leave_type": leave_type,
                        "from_date": start_date,
                        "to_date": end_date,
                        "docstatus": 1
                    })
                
                if existing_allocation:
                    skipped_count += 1
                    frappe.log_error(
                        f"Skipped new year allocation for employee {employee['employee_name']} ({employee['custom_contract_type']}) - Already exists",
                        "New Year Leave Allocation Skip Log"
                    )
                    continue

                # Create new allocation for the year
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
                created_count += 1
                
                frappe.log_error(
                    f"Created new year allocation for employee {employee['employee_name']} ({employee['custom_contract_type']}): "
                    f"Days allocated: {leave_days}",
                    "New Year Leave Allocation Create Log"
                )
                
                frappe.db.commit()

            except Exception as e:
                error_count += 1
                error_details.append(f"Error for {employee['employee_name']} ({employee.get('custom_contract_type', 'N/A')}): {str(e)}")
                frappe.log_error(
                    f"Error creating new year allocation for employee {employee['name']}: {str(e)}", 
                    "New Year Leave Allocation Error"
                )

        # Prepare detailed success message
        success_message = f"""
        <strong>New Year Leave Allocation Summary:</strong><br>
        - Created allocations: {created_count} employees<br>
        - Skipped (existing): {skipped_count} employees<br>
        - Failed: {error_count} employees
        """

        if error_details:
            error_details_html = "<br>".join(error_details)
            success_message += f"<br><br><strong>Error Details:</strong><br>{error_details_html}"

        # Send email notification
        send_email_notification(
            leave_allocation_settings_data,
            success_message=success_message,
            hr_email=hr_email
        )

        return {
            "message": f"Created {created_count} allocations, skipped {skipped_count}, failed {error_count}",
            "created": created_count,
            "skipped": skipped_count,
            "failed": error_count,
            "eligible_contract_types": contract_types_with_leave,
            "total_eligible_employees": len(employees)
        }

    except Exception as e:
        error_message = str(e)
        error_traceback = traceback.format_exc()
        
        frappe.log_error(
            f"Error in new year leave allocation process: {error_message}\n{error_traceback}", 
            "New Year Leave Allocation Error"
        )
        
        # Try to get hr_email for error notification
        try:
            hr_email = frappe.get_doc("Leave Allocation Setting").hr_email
        except:
            hr_email = None
            
        if hr_email:
            send_email_notification(
                error_message=error_message, 
                error_traceback=error_traceback, 
                hr_email=hr_email
            )
        
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
            
            <p>An error occurred while updating the leave allocations:</p>
            
            <div style="background-color: #fff3f3; padding: 15px; border-left: 4px solid #ff0000; margin: 10px 0;">
                <strong>Error Message:</strong><br>
                {error_message}
            </div>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #666; margin: 10px 0;">
                <strong>Traceback:</strong><br>
                <pre style="white-space: pre-wrap;">{error_traceback}</pre>
            </div>
            
            <p>Best regards,<br>ERPNext HR Leave Allocation</p>
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
            
            <p>Best regards,<br>ERPNext HR Leave Allocation</p>
        </div>
        """

    frappe.sendmail(
        recipients=hr_email,
        subject=subject,
        message=message
    )