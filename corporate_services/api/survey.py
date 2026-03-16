import frappe
from frappe import _  # type: ignore


ADMIN_ROLES = ["System Manager", "HR Manager"]


def _require_admin() -> None:
    frappe.only_for(ADMIN_ROLES)


@frappe.whitelist()
def get_surveys():
    \"\"\"List all surveys for the admin UI (including unpublished).\"\"\"
    _require_admin()
    return frappe.get_all(
        "Survey",
        fields=[
            "name",
            "title",
            "year",
            "is_published",
            "departments",
            "total_submissions",
            "modified",
        ],
        order_by="modified desc",
    )


@frappe.whitelist(allow_guest=True)
def get_survey_detail(survey: str):
    \"\"\"Load full survey structure (sections + questions).

    For guests, only return data if the survey is published.
    \"\"\"
    doc = frappe.get_doc("Survey", survey)

    if frappe.session.user == "Guest" and not doc.is_published:
        frappe.throw(_("Survey is not published"), frappe.PermissionError)

    doc_dict = doc.as_dict()
    # Ensure children are loaded as plain lists
    doc_dict["sections"] = [
        {
            **section.as_dict(),
            "questions": [q.as_dict() for q in section.questions],
        }
        for section in doc.sections
    ]
    return doc_dict


@frappe.whitelist()
def set_survey_published(survey: str, is_published: int | str):
    \"\"\"Toggle publish / hide for a survey (admin only).\"\"\"
    _require_admin()
    value = 1 if str(is_published) in {"1", "true", "True"} else 0
    doc = frappe.get_doc("Survey", survey)
    doc.is_published = value
    doc.save()
    frappe.db.commit()
    return {"name": doc.name, "is_published": doc.is_published}


@frappe.whitelist(allow_guest=True)
def get_public_surveys():
    \"\"\"List only published surveys (for public index or preview).\"\"\"
    return frappe.get_all(
        "Survey",
        filters={"is_published": 1},
        fields=["name", "title", "year", "departments"],
        order_by="year desc, modified desc",
    )


@frappe.whitelist(allow_guest=True)
def submit_survey_response(survey: str, department: str | None = None, answers: list | None = None):
    \"\"\"Create Survey Response + Survey Answer docs for a public submission.

    `answers` should be a list of objects: { question: str, value: str, follow_up: str | null }.
    \"\"\"  # noqa: E501
    survey_doc = frappe.get_doc("Survey", survey)
    if not survey_doc.is_published:
        frappe.throw(_("Survey is not accepting responses"), frappe.PermissionError)

    if answers is None:
        answers = []

    resp = frappe.new_doc("Survey Response")
    resp.survey = survey_doc.name
    resp.department = department or None

    for item in answers:
        if not item:
            continue
        child = resp.append("answers", {})
        child.question = item.get("question")
        child.value = item.get("value") or ""
        child.follow_up = item.get("follow_up") or None

    resp.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"name": resp.name}


@frappe.whitelist()
def get_survey_responses(survey: str):
    \"\"\"List responses for a given survey (admin/HR only).\"\"\"
    _require_admin()
    return frappe.get_all(
        "Survey Response",
        filters={"survey": survey},
        fields=["name", "survey", "department", "creation", "modified"],
        order_by="creation desc",
    )

