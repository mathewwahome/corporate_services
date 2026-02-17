import frappe
from frappe.utils import get_fullname, add_days, now_datetime, getdate, nowdate, get_datetime
from datetime import datetime, time

@frappe.whitelist()
def create_onboarding_tasks(employee_name):
    """
    Creates a task list for pre-boarding and onboarding when employee profile is created.
    Sends notification to HR immediately.
    
    Args:
        employee_name (str): Name of the Employee document.
    
    Returns:
        dict: Summary of tasks created.
    """
    employee = frappe.get_doc("Employee", employee_name)
    
    if not employee.date_of_joining:
        frappe.throw("Employee must have a Date of Joining to create onboarding tasks.")
    
    company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")
    
    # Define onboarding task checklist
    tasks = [
        # Pre-boarding tasks (before start date)
        {
            "title": f"Send offer letter to {employee.employee_name}",
            "description": "Prepare and send formal offer letter with terms and conditions",
            "due_date": add_days(employee.date_of_joining, -14),
            "category": "Pre-boarding",
            "priority": "High"
        },
        {
            "title": f"Create email account for {employee.employee_name}",
            "description": "Set up company email account and send credentials",
            "due_date": add_days(employee.date_of_joining, -7),
            "category": "Pre-boarding",
            "priority": "High"
        },
        {
            "title": f"Prepare workstation for {employee.employee_name}",
            "description": "Set up desk, computer, phone, and office supplies",
            "due_date": add_days(employee.date_of_joining, -3),
            "category": "Pre-boarding",
            "priority": "Medium"
        },
        {
            "title": f"Send welcome email to {employee.employee_name}",
            "description": "Send welcome email with onboarding schedule and first day details",
            "due_date": add_days(employee.date_of_joining, -1),
            "category": "Pre-boarding",
            "priority": "High"
        },
        # Day 1 tasks
        {
            "title": f"Conduct office tour for {employee.employee_name}",
            "description": "Show facilities, introduce to team members, explain office layout",
            "due_date": employee.date_of_joining,
            "category": "Day 1",
            "priority": "High"
        },
        {
            "title": f"Complete HR documentation for {employee.employee_name}",
            "description": "Collect signed contracts, tax forms, bank details, ID copies",
            "due_date": employee.date_of_joining,
            "category": "Day 1",
            "priority": "High"
        },
        {
            "title": f"Assign mentor/buddy to {employee.employee_name}",
            "description": "Introduce to assigned mentor for ongoing support",
            "due_date": employee.date_of_joining,
            "category": "Day 1",
            "priority": "Medium"
        },
        # Week 1 tasks
        {
            "title": f"Schedule systems training for {employee.employee_name}",
            "description": "Provide training on company systems, software, and tools",
            "due_date": add_days(employee.date_of_joining, 3),
            "category": "Week 1",
            "priority": "Medium"
        },
        {
            "title": f"Review job description with {employee.employee_name}",
            "description": "Discuss role expectations, objectives, and performance metrics",
            "due_date": add_days(employee.date_of_joining, 5),
            "category": "Week 1",
            "priority": "High"
        },
        # 30-day tasks
        {
            "title": f"Send 30-day feedback survey to {employee.employee_name}",
            "description": "Request feedback on onboarding experience",
            "due_date": add_days(employee.date_of_joining, 30),
            "category": "30 Days",
            "priority": "Medium"
        },
        {
            "title": f"Send policy comprehension quiz to {employee.employee_name}",
            "description": "Assess understanding of company policies and procedures",
            "due_date": add_days(employee.date_of_joining, 30),
            "category": "30 Days",
            "priority": "Medium"
        },
        # 90-day tasks
        {
            "title": f"Schedule probation review for {employee.employee_name}",
            "description": "Conduct formal probation review meeting with supervisor",
            "due_date": add_days(employee.date_of_joining, 90),
            "category": "90 Days",
            "priority": "High"
        },
        {
            "title": f"Complete probation assessment for {employee.employee_name}",
            "description": "Evaluate performance and confirm permanent employment",
            "due_date": add_days(employee.date_of_joining, 90),
            "category": "90 Days",
            "priority": "High"
        }
    ]
    
    created_tasks = []
    
    # Create tasks in the system
    for task_data in tasks:
        try:
            task = frappe.get_doc({
                "doctype": "Task",
                "subject": task_data["title"],
                "description": task_data["description"],
                "exp_end_date": task_data["due_date"],
                "priority": task_data["priority"],
                "status": "Open",
                "custom_category": task_data["category"],
                "custom_employee": employee_name
            })
            task.insert(ignore_permissions=True)
            created_tasks.append(task.name)
        except Exception as e:
            frappe.log_error(
                message=f"Failed to create task: {task_data['title']}. Error: {str(e)}",
                title=f"Onboarding Task Creation Failed - {employee_name}"
            )
    
    # Send notification to HR
    send_task_list_notification_to_hr(employee, created_tasks)
    
    return {
        "success": True,
        "message": f"{len(created_tasks)} onboarding tasks created for {employee.employee_name}",
        "tasks_created": len(created_tasks),
        "employee": employee_name
    }


def send_task_list_notification_to_hr(employee, task_list):
    """
    Sends notification to HR that onboarding task list has been created.
    
    Args:
        employee (Document): Employee document.
        task_list (list): List of created task names.
    """
    hr_emails = get_hr_emails()
    
    if not hr_emails:
        frappe.log_error("No HR email addresses found for onboarding notification.")
        return
    
    company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")
    
    email_message = f"""
    <p>Hello HR Team,</p>
    
    <p>An onboarding task list has been created for new employee <strong>{employee.employee_name}</strong>.</p>
    
    <p><strong>Employee Details:</strong><br>
    Name: {employee.employee_name}<br>
    Employee ID: {employee.name}<br>
    Designation: {employee.designation or 'N/A'}<br>
    Department: {employee.department or 'N/A'}<br>
    Date of Joining: {employee.date_of_joining}</p>
    
    <p><strong>Tasks Created:</strong> {len(task_list)}</p>
    
    <p>Please review the onboarding checklist and assign tasks as needed.</p>
    
    <p>Best regards,<br>
    HR System<br>
    {company_name}</p>
    """
    
    frappe.sendmail(
        recipients=hr_emails,
        subject=f"Onboarding Tasks Created - {employee.employee_name}",
        message=email_message
    )


@frappe.whitelist()
def send_welcome_email_day1(employee_name):
    """
    Sends welcome email with onboarding schedule to new hire on Day 1 at 08:00.
    
    Args:
        employee_name (str): Name of the Employee document.
    
    Returns:
        str: Status message.
    """
    employee = frappe.get_doc("Employee", employee_name)
    
    if not employee.personal_email and not employee.company_email:
        frappe.throw(f"No email found for employee {employee.employee_name}.")
    
    recipient_email = employee.company_email or employee.personal_email
    company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")
    
    email_message = f"""
    <p>Dear {employee.employee_name},</p>
    
    <p>Welcome to <strong>{company_name}</strong>! We are thrilled to have you join our team.</p>
    
    <p><strong>Your First Day Schedule:</strong></p>
    <ul>
        <li><strong>08:30 AM</strong> - Check in at Reception</li>
        <li><strong>09:00 AM</strong> - HR Orientation & Documentation</li>
        <li><strong>10:30 AM</strong> - Office Tour & Team Introductions</li>
        <li><strong>12:00 PM</strong> - Lunch with Your Team</li>
        <li><strong>01:30 PM</strong> - IT Setup & System Access</li>
        <li><strong>03:00 PM</strong> - Meet Your Supervisor</li>
        <li><strong>04:30 PM</strong> - Welcome Session & Q&A</li>
    </ul>
    
    <p><strong>What to Bring:</strong></p>
    <ul>
        <li>Valid ID (National ID/Passport)</li>
        <li>Signed employment contract</li>
        <li>Bank details for salary processing</li>
        <li>Academic certificates (originals for verification)</li>
        <li>Passport-size photos (2 copies)</li>
    </ul>
    
    <p>If you have any questions before your first day, please don't hesitate to reach out.</p>
    
    <p>We look forward to seeing you!</p>
    
    <p>Best regards,<br>
    HR Team<br>
    {company_name}</p>
    """
    
    frappe.sendmail(
        recipients=[recipient_email],
        subject=f"Welcome to {company_name} - Your First Day",
        message=email_message
    )
    
    employee.add_comment("Comment", "Welcome email sent for Day 1")
    
    return f"Welcome email sent to {employee.employee_name}"


@frappe.whitelist()
def send_company_wide_introduction(employee_name):
    """
    Sends company-wide introduction email for new employee on Day 1 at 08:00.
    
    Args:
        employee_name (str): Name of the Employee document.
    
    Returns:
        str: Status message.
    """
    employee = frappe.get_doc("Employee", employee_name)
    company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")
    
    # Get all active employee emails
    all_employees = frappe.get_all(
        "Employee",
        filters={"status": "Active", "company_email": ["!=", ""]},
        fields=["company_email"]
    )
    
    recipient_emails = [emp.company_email for emp in all_employees if emp.company_email]
    
    if not recipient_emails:
        frappe.throw("No employee emails found for company-wide announcement.")
    
    email_message = f"""
    <p>Dear Team,</p>
    
    <p>We are excited to announce that <strong>{employee.employee_name}</strong> is joining 
    {company_name} today as <strong>{employee.designation or 'our new team member'}</strong> 
    in the <strong>{employee.department or ''}</strong> department.</p>
    
    <p><strong>About {employee.employee_name.split()[0]}:</strong><br>
    {employee.employee_name} brings valuable experience and skills to our team. 
    Please join us in welcoming them warmly and helping them settle in.</p>
    
    <p>You can reach {employee.employee_name.split()[0]} at: 
    <a href="mailto:{employee.company_email}">{employee.company_email or 'TBD'}</a></p>
    
    <p>Let's make {employee.employee_name.split()[0]}'s first day memorable!</p>
    
    <p>Best regards,<br>
    HR Team<br>
    {company_name}</p>
    """
    
    frappe.sendmail(
        recipients=recipient_emails,
        subject=f"Welcome Our Newest Team Member - {employee.employee_name}",
        message=email_message
    )
    
    employee.add_comment("Comment", "Company-wide introduction email sent")
    
    return f"Introduction email sent to all staff about {employee.employee_name}"


@frappe.whitelist()
def confirm_handover_to_supervisor(employee_name):
    """
    Sends confirmation to HR at end of Day 1 to confirm handover to supervisor.
    
    Args:
        employee_name (str): Name of the Employee document.
    
    Returns:
        str: Status message.
    """
    employee = frappe.get_doc("Employee", employee_name)
    hr_emails = get_hr_emails()
    
    if not hr_emails:
        frappe.throw("No HR email addresses found.")
    
    company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")
    supervisor_name = employee.reports_to
    supervisor_email = None
    
    if supervisor_name:
        supervisor = frappe.get_doc("Employee", supervisor_name)
        supervisor_email = supervisor.company_email
    
    email_message = f"""
    <p>Hello HR Team,</p>
    
    <p>This is a reminder to confirm the handover of <strong>{employee.employee_name}</strong> 
    to their supervisor at the end of Day 1.</p>
    
    <p><strong>Employee Details:</strong><br>
    Name: {employee.employee_name}<br>
    Designation: {employee.designation or 'N/A'}<br>
    Department: {employee.department or 'N/A'}<br>
    Supervisor: {supervisor.employee_name if supervisor_name else 'Not Assigned'}</p>
    
    <p><strong>Action Required:</strong><br>
    Please confirm that the following have been completed:</p>
    <ul>
        <li>All Day 1 documentation collected</li>
        <li>System access granted</li>
        <li>Introduction to supervisor completed</li>
        <li>Workspace prepared and functional</li>
        <li>First week schedule communicated</li>
    </ul>
    
    <p>Best regards,<br>
    HR System<br>
    {company_name}</p>
    """
    
    frappe.sendmail(
        recipients=hr_emails,
        subject=f"Day 1 Handover Confirmation - {employee.employee_name}",
        message=email_message
    )
    
    return f"Handover confirmation request sent to HR for {employee.employee_name}"


@frappe.whitelist()
def send_30day_feedback_survey(employee_name):
    """
    Sends 30-day feedback survey request to new hire.
    
    Args:
        employee_name (str): Name of the Employee document.
    
    Returns:
        str: Status message.
    """
    employee = frappe.get_doc("Employee", employee_name)
    
    if not employee.company_email:
        frappe.throw(f"No company email found for employee {employee.employee_name}.")
    
    company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")
    
    # You can replace this with actual survey link
    survey_link = f"{frappe.utils.get_url()}/onboarding-survey?employee={employee_name}"
    
    email_message = f"""
    <p>Dear {employee.employee_name},</p>
    
    <p>Congratulations on completing your first 30 days at <strong>{company_name}</strong>!</p>
    
    <p>We value your feedback and would like to hear about your onboarding experience. 
    Your insights will help us improve the onboarding process for future team members.</p>
    
    <p><strong>Please complete this brief survey:</strong><br>
    <a href="{survey_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; 
    text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">
    Take Survey (5 minutes)</a></p>
    
    <p><strong>Survey Topics:</strong></p>
    <ul>
        <li>Pre-boarding experience</li>
        <li>First day orientation</li>
        <li>Training and resources provided</li>
        <li>Team integration</li>
        <li>Overall satisfaction</li>
    </ul>
    
    <p>Thank you for your time and feedback!</p>
    
    <p>Best regards,<br>
    HR Team<br>
    {company_name}</p>
    """
    
    frappe.sendmail(
        recipients=[employee.company_email],
        subject=f"Your Feedback Matters - 30-Day Onboarding Survey",
        message=email_message
    )
    
    employee.add_comment("Comment", "30-day feedback survey sent")
    
    return f"30-day feedback survey sent to {employee.employee_name}"


@frappe.whitelist()
def send_policy_comprehension_quiz(employee_name):
    """
    Sends policy comprehension quiz to new hire at 30 days.
    
    Args:
        employee_name (str): Name of the Employee document.
    
    Returns:
        str: Status message.
    """
    employee = frappe.get_doc("Employee", employee_name)
    
    if not employee.company_email:
        frappe.throw(f"No company email found for employee {employee.employee_name}.")
    
    company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")
    
    # Replace with actual quiz link
    quiz_link = f"{frappe.utils.get_url()}/policy-quiz?employee={employee_name}"
    
    email_message = f"""
    <p>Dear {employee.employee_name},</p>
    
    <p>As part of your onboarding at <strong>{company_name}</strong>, we require all new employees 
    to complete a policy comprehension quiz to ensure understanding of our key policies and procedures.</p>
    
    <p><strong>Please complete the quiz by clicking below:</strong><br>
    <a href="{quiz_link}" style="background-color: #2196F3; color: white; padding: 10px 20px; 
    text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">
    Start Quiz (15 minutes)</a></p>
    
    <p><strong>Quiz Coverage:</strong></p>
    <ul>
        <li>Code of Conduct</li>
        <li>Data Privacy & Security</li>
        <li>Health & Safety Policies</li>
        <li>Leave & Attendance</li>
        <li>Anti-Harassment Policy</li>
        <li>Confidentiality & IP Rights</li>
    </ul>
    
    <p><strong>Important Notes:</strong></p>
    <ul>
        <li>You must score at least 80% to pass</li>
        <li>You can retake the quiz if needed</li>
        <li>Results will be shared with HR</li>
    </ul>
    
    <p>If you have any questions, please contact HR.</p>
    
    <p>Best regards,<br>
    HR Team<br>
    {company_name}</p>
    """
    
    frappe.sendmail(
        recipients=[employee.company_email],
        subject=f"Action Required: Policy Comprehension Quiz",
        message=email_message
    )
    
    employee.add_comment("Comment", "Policy comprehension quiz sent")
    
    return f"Policy quiz sent to {employee.employee_name}"


@frappe.whitelist()
def send_probation_review_tasks(employee_name):
    """
    Sends probation review tasks to supervisor and new hire at 90 days.
    
    Args:
        employee_name (str): Name of the Employee document.
    
    Returns:
        str: Status message.
    """
    employee = frappe.get_doc("Employee", employee_name)
    
    if not employee.company_email:
        frappe.throw(f"No company email found for employee {employee.employee_name}.")
    
    company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")
    
    supervisor_email = None
    supervisor_name = "Your Supervisor"
    
    if employee.reports_to:
        supervisor = frappe.get_doc("Employee", employee.reports_to)
        supervisor_email = supervisor.company_email
        supervisor_name = supervisor.employee_name
    
    # Email to new hire
    employee_message = f"""
    <p>Dear {employee.employee_name},</p>
    
    <p>Your 90-day probation period at <strong>{company_name}</strong> is coming to an end. 
    We will be conducting a probation review to assess your performance and confirm your permanent employment.</p>
    
    <p><strong>What to Expect:</strong></p>
    <ul>
        <li>Meeting with your supervisor: {supervisor_name}</li>
        <li>Performance evaluation discussion</li>
        <li>Feedback on achievements and areas for improvement</li>
        <li>Decision on probation completion</li>
    </ul>
    
    <p><strong>Please Prepare:</strong></p>
    <ul>
        <li>Self-assessment of your performance</li>
        <li>List of key achievements in the past 90 days</li>
        <li>Challenges faced and how you addressed them</li>
        <li>Questions or feedback for your supervisor</li>
    </ul>
    
    <p>Your supervisor will schedule the review meeting shortly.</p>
    
    <p>Best regards,<br>
    HR Team<br>
    {company_name}</p>
    """
    
    frappe.sendmail(
        recipients=[employee.company_email],
        subject=f"90-Day Probation Review - Action Required",
        message=employee_message
    )
    
    # Email to supervisor (if exists)
    if supervisor_email:
        supervisor_message = f"""
        <p>Dear {supervisor_name},</p>
        
        <p><strong>{employee.employee_name}</strong> has reached their 90-day probation milestone. 
        Please complete the probation review process.</p>
        
        <p><strong>Employee Details:</strong><br>
        Name: {employee.employee_name}<br>
        Designation: {employee.designation or 'N/A'}<br>
        Department: {employee.department or 'N/A'}<br>
        Date of Joining: {employee.date_of_joining}</p>
        
        <p><strong>Action Required:</strong></p>
        <ol>
            <li>Schedule a probation review meeting with {employee.employee_name.split()[0]}</li>
            <li>Complete the performance evaluation form</li>
            <li>Provide written feedback on performance</li>
            <li>Recommend: Confirm / Extend Probation / Terminate</li>
            <li>Submit review to HR within 7 days</li>
        </ol>
        
        <p><strong>Evaluation Criteria:</strong></p>
        <ul>
            <li>Job knowledge and technical skills</li>
            <li>Quality and quantity of work</li>
            <li>Communication and teamwork</li>
            <li>Initiative and problem-solving</li>
            <li>Attendance and punctuality</li>
            <li>Adherence to company policies</li>
        </ul>
        
        <p>If you need any support or have questions, please contact HR.</p>
        
        <p>Best regards,<br>
        HR Team<br>
        {company_name}</p>
        """
        
        frappe.sendmail(
            recipients=[supervisor_email],
            subject=f"Probation Review Due - {employee.employee_name}",
            message=supervisor_message
        )
    
    employee.add_comment("Comment", "90-day probation review notifications sent")
    
    return f"Probation review tasks sent to {employee.employee_name} and supervisor"


@frappe.whitelist()
def send_overdue_task_reminders():
    """
    Sends daily reminders for overdue onboarding tasks to task owners and HR.
    This function should be scheduled to run daily via a scheduled job.
    
    Returns:
        dict: Summary of reminders sent.
    """
    # Get all overdue onboarding tasks
    overdue_tasks = frappe.get_all(
        "Task",
        filters={
            "status": ["!=", "Completed"],
            "exp_end_date": ["<", nowdate()],
            "custom_employee": ["!=", ""]
        },
        fields=["name", "subject", "exp_end_date", "assigned_to", "custom_employee", "priority"]
    )
    
    if not overdue_tasks:
        return {
            "success": True,
            "message": "No overdue onboarding tasks found.",
            "reminders_sent": 0
        }
    
    hr_emails = get_hr_emails()
    reminders_sent = 0
    
    for task in overdue_tasks:
        try:
            # Calculate days overdue
            days_overdue = (getdate(nowdate()) - getdate(task.exp_end_date)).days
            
            # Get task owner
            task_owner_email = None
            if task.assigned_to:
                task_owner = frappe.db.get_value("User", task.assigned_to, "email")
                task_owner_email = task_owner
            
            # Get employee details
            employee = frappe.get_doc("Employee", task.custom_employee)
            company_name = employee.company or frappe.db.get_single_value("Global Defaults", "default_company")
            
            # Build email message
            email_message = f"""
            <p><strong>OVERDUE ONBOARDING TASK REMINDER</strong></p>
            
            <p>The following onboarding task is <strong style="color: red;">{days_overdue} day(s) overdue</strong>:</p>
            
            <p><strong>Task Details:</strong><br>
            Task: {task.subject}<br>
            Employee: {employee.employee_name}<br>
            Due Date: {task.exp_end_date}<br>
            Priority: {task.priority}<br>
            Days Overdue: {days_overdue}</p>
            
            <p>Please complete this task as soon as possible to ensure a smooth onboarding experience.</p>
            
            <p>Best regards,<br>
            HR System<br>
            {company_name}</p>
            """
            
            # Send to task owner
            recipients = []
            if task_owner_email:
                recipients.append(task_owner_email)
            
            # Always copy HR
            if hr_emails:
                recipients.extend(hr_emails)
            
            # Remove duplicates
            recipients = list(set(recipients))
            
            if recipients:
                frappe.sendmail(
                    recipients=recipients,
                    subject=f"OVERDUE: Onboarding Task - {employee.employee_name}",
                    message=email_message,
                    priority=1  # High priority
                )
                reminders_sent += 1
                
        except Exception as e:
            frappe.log_error(
                message=f"Failed to send overdue reminder for task {task.name}: {str(e)}",
                title=f"Overdue Task Reminder Failed - {task.name}"
            )
    
    return {
        "success": True,
        "message": f"{reminders_sent} overdue task reminders sent.",
        "reminders_sent": reminders_sent
    }


def get_hr_emails():
    """
    Helper function to get all HR user emails.
    
    Returns:
        list: List of HR email addresses.
    """
    # Get users with HR role
    hr_users = frappe.get_all(
        "Has Role",
        filters={"role": "HR Manager"},
        fields=["parent"]
    )
    
    hr_emails = []
    for user in hr_users:
        email = frappe.db.get_value("User", user.parent, "email")
        if email:
            hr_emails.append(email)
    
    # Fallback: get HR department employees
    if not hr_emails:
        hr_employees = frappe.get_all(
            "Employee",
            filters={"department": "Human Resources", "status": "Active"},
            fields=["company_email"]
        )
        hr_emails = [emp.company_email for emp in hr_employees if emp.company_email]
    
    return list(set(hr_emails))  # Remove duplicates


# Scheduled job functions (to be added to Frappe scheduler)

def schedule_day1_welcome_email():
    """
    Scheduled job to send welcome emails at 08:00 on start date.
    Add to hooks.py:
    scheduler_events = {
        "cron": {
            "0 8 * * *": [
                "your_app.onboarding_notifications.schedule_day1_welcome_email"
            ]
        }
    }
    """
    today = nowdate()
    
    # Get all employees starting today
    new_hires = frappe.get_all(
        "Employee",
        filters={"date_of_joining": today, "status": "Active"},
        fields=["name", "employee_name"]
    )
    
    for hire in new_hires:
        try:
            send_welcome_email_day1(hire.name)
            send_company_wide_introduction(hire.name)
        except Exception as e:
            frappe.log_error(
                message=f"Failed to send Day 1 emails for {hire.name}: {str(e)}",
                title=f"Day 1 Email Failed - {hire.name}"
            )


def schedule_30day_notifications():
    """
    Scheduled job to send 30-day feedback and quiz.
    Add to hooks.py scheduler.
    """
    date_30_days_ago = add_days(nowdate(), -30)
    
    employees = frappe.get_all(
        "Employee",
        filters={"date_of_joining": date_30_days_ago, "status": "Active"},
        fields=["name"]
    )
    
    for emp in employees:
        try:
            send_30day_feedback_survey(emp.name)
            send_policy_comprehension_quiz(emp.name)
        except Exception as e:
            frappe.log_error(
                message=f"Failed to send 30-day notifications for {emp.name}: {str(e)}",
                title=f"30-Day Notification Failed - {emp.name}"
            )


def schedule_90day_probation_review():
    """
    Scheduled job to send 90-day probation review tasks.
    Add to hooks.py scheduler.
    """
    date_90_days_ago = add_days(nowdate(), -90)
    
    employees = frappe.get_all(
        "Employee",
        filters={"date_of_joining": date_90_days_ago, "status": "Active"},
        fields=["name"]
    )
    
    for emp in employees:
        try:
            send_probation_review_tasks(emp.name)
        except Exception as e:
            frappe.log_error(
                message=f"Failed to send 90-day review for {emp.name}: {str(e)}",
                title=f"90-Day Review Failed - {emp.name}"
            )


def schedule_end_of_day1_confirmation():
    """
    Scheduled job to send end-of-day handover confirmation at 17:00.
    Add to hooks.py:
    "cron": {
        "0 17 * * *": [
            "your_app.onboarding_notifications.schedule_end_of_day1_confirmation"
        ]
    }
    """
    today = nowdate()
    
    new_hires = frappe.get_all(
        "Employee",
        filters={"date_of_joining": today, "status": "Active"},
        fields=["name"]
    )
    
    for hire in new_hires:
        try:
            confirm_handover_to_supervisor(hire.name)
        except Exception as e:
            frappe.log_error(
                message=f"Failed to send Day 1 confirmation for {hire.name}: {str(e)}",
                title=f"Day 1 Confirmation Failed - {hire.name}"
            )