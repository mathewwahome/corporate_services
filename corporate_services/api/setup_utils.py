import frappe
import os
import json
from frappe.utils.fixtures import sync_fixtures




def clear_workspaces():
    try:
        frappe.logger().info("Starting the process to delete unnecessary workspaces.")
        
        # Get the list of workspaces to delete
        workspaces_to_delete = frappe.get_list("Workspace", filters={"module": ["!=", "ICL Corporate Services"]})
        
        frappe.logger().info(f"Workspaces to delete: {workspaces_to_delete}")
        
        # Iterate through the list and delete each workspace
        for workspace in workspaces_to_delete:
            frappe.delete_doc("Workspace", workspace['name'], force=True)
            frappe.logger().info(f"Deleted workspace: {workspace['name']}")
        
        # Commit the transaction to apply the changes
        frappe.db.commit()
        frappe.logger().info("Deletion process completed successfully.")
    
    except Exception as e:
        frappe.logger().error(f"An error occurred while deleting workspaces: {e}")
        frappe.db.rollback()  # Rollback in case of error
    return


def force_sync_fixtures():
    """Force sync all fixtures on every migrate"""
    frappe.logger().info("=" * 60)
    frappe.logger().info("Force syncing ICL Corporate Servises fixtures...")
    frappe.logger().info("=" * 60)

    fixture_path = frappe.get_app_path("corporate_services", "fixtures")

    # List of fixture files to sync
    fixture_files = {
        "workflow.json": "Workflow",
        "workflow_state.json": "Workflow State",
        "workflow_action_master.json": "Workflow Action Master",
        "email_template.json": "Email Template",
        "client_script.json": "Client Script",
        "role.json": "Role",
        "role_profile.json": "Role Profile",
        "print_format.json": "Print Format",
        "workspace.json": "Workspace",
        "custom_docperm.json":"Custom DocPerm",
    }

    for filename, doctype in fixture_files.items():
        file_path = os.path.join(fixture_path, filename)

        if not os.path.exists(file_path):
            frappe.logger().info(f"⊘ Skipping {doctype} - file not found")
            continue

        try:
            with open(file_path, 'r') as f:
                docs = json.load(f)

            if not docs:
                continue

            for doc_data in docs:
                doc_name = doc_data.get("name")

                try:
                    if frappe.db.exists(doctype, doc_name):
                        doc = frappe.get_doc(doctype, doc_name)
                        doc.update(doc_data)
                        doc.flags.ignore_permissions = True
                        doc.flags.ignore_mandatory = True
                        doc.flags.ignore_validate = True
                        doc.save()
                        frappe.logger().info(f"Updated {doctype}: {doc_name}")
                    else:
                        doc = frappe.get_doc(doc_data)
                        doc.flags.ignore_permissions = True
                        doc.flags.ignore_mandatory = True
                        doc.insert()
                        frappe.logger().info(f"Created {doctype}: {doc_name}")

                except Exception as e:
                    frappe.logger().error(f"Error with {doctype} '{doc_name}': {str(e)}")

            frappe.db.commit()

        except Exception as e:
            frappe.logger().error(f"Error loading {filename}: {str(e)}")

    frappe.logger().info("=" * 60)
    frappe.logger().info("Fixture sync completed!")
    frappe.logger().info("=" * 60)
    

def post_install():
    force_sync_fixtures()
    clear_workspaces()
    return



    