from frappe import delete_doc
import frappe




def clear_workspaces():
    workspaces_to_delete = frappe.get_list("Workspace", filters={"module":[ "!=", "ICL Corporate Services"]})
    for workspace in workspaces_to_delete:
        res = delete_doc("Workspace", workspace)
        print(res)
    frappe.db.commit()
    return


def post_install():
    clear_workspaces()
    return



    