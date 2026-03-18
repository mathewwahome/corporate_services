import frappe
from frappe import _  # type: ignore
from collections import Counter


ADMIN_ROLES = ["System Manager", "HR Manager"]


def _require_admin() -> None:
    frappe.only_for(ADMIN_ROLES)


# ---------------------------------------------------------------------------
# Survey Response event handlers (wired via hooks.py doc_events)
# ---------------------------------------------------------------------------

def on_survey_response_insert(doc, method=None):
    """Atomically increment total_submissions on the parent Survey."""
    frappe.db.sql(
        "UPDATE `tabSurvey` SET total_submissions = total_submissions + 1 WHERE name = %s",
        doc.survey,
    )


def on_survey_response_delete(doc, method=None):
    """Atomically decrement total_submissions on the parent Survey (floor 0)."""
    frappe.db.sql(
        "UPDATE `tabSurvey` SET total_submissions = GREATEST(total_submissions - 1, 0) WHERE name = %s",
        doc.survey,
    )


# ---------------------------------------------------------------------------
# Admin APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_surveys():
    """List all surveys for the admin UI (including unpublished)."""
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


@frappe.whitelist()
def set_survey_published(survey: str, is_published: int | str):
    """Toggle publish / hide for a survey (admin only)."""
    _require_admin()
    value = 1 if str(is_published) in {"1", "true", "True"} else 0
    doc = frappe.get_doc("Survey", survey)
    doc.is_published = value
    doc.save()
    frappe.db.commit()
    return {"name": doc.name, "is_published": doc.is_published}


@frappe.whitelist()
def get_survey_responses(survey: str):
    """List responses for a given survey (admin/HR only)."""
    _require_admin()
    return frappe.get_all(
        "Survey Response",
        filters={"survey": survey},
        fields=["name", "survey", "department", "creation", "modified"],
        order_by="creation desc",
    )


@frappe.whitelist()
def get_survey_analytics(survey: str):
    """Return aggregated answer data per question for a survey (admin only)."""
    _require_admin()

    total = frappe.db.count("Survey Response", {"survey": survey})

    # All answers for responses in this survey
    answers = frappe.db.sql(
        """
        SELECT sa.question, sa.value
        FROM `tabSurvey Answer` sa
        JOIN `tabSurvey Response` sr ON sr.name = sa.parent
        WHERE sr.survey = %s
        """,
        survey,
        as_dict=True,
    )

    answer_map: dict[str, list[str]] = {}
    for a in answers:
        answer_map.setdefault(a.question, []).append(a.value or "")

    survey_doc = frappe.get_doc("Survey", survey)
    questions = []
    for section in sorted(survey_doc.sections, key=lambda s: s.order or 0):
        for q in sorted(section.questions, key=lambda x: x.order or 0):
            values = answer_map.get(q.name, [])
            non_empty = [v for v in values if v]

            if q.question_type in ("SINGLE_SELECT", "MULTI_SELECT"):
                all_selections: list[str] = []
                for v in non_empty:
                    all_selections.extend(v.split("|||"))
                aggregation = dict(Counter(all_selections))
            elif q.question_type == "RATING":
                aggregation = dict(Counter(non_empty))
            else:
                aggregation = {}

            questions.append(
                {
                    "name": q.name,
                    "section": section.title,
                    "question_text": q.question_text,
                    "question_type": q.question_type,
                    "response_count": len(non_empty),
                    "aggregation": aggregation,
                    "text_responses": non_empty if q.question_type == "TEXT" else [],
                }
            )

    return {"total_responses": total, "questions": questions}


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_public_surveys():
    """List only published surveys (for public index or preview)."""
    return frappe.get_all(
        "Survey",
        filters={"is_published": 1},
        fields=["name", "title", "year", "departments"],
        order_by="year desc, modified desc",
    )


@frappe.whitelist(allow_guest=True)
def get_survey_detail(survey: str):
    """Load full survey structure (sections + questions).

    For guests, only return data if the survey is published.
    """
    doc = frappe.get_doc("Survey", survey)

    if frappe.session.user == "Guest" and not doc.is_published:
        frappe.throw(_("Survey is not published"), frappe.PermissionError)

    doc_dict = doc.as_dict()
    doc_dict["sections"] = [
        {
            **section.as_dict(),
            "questions": sorted(
                [q.as_dict() for q in section.questions],
                key=lambda q: q.get("order") or 0,
            ),
        }
        for section in sorted(doc.sections, key=lambda s: s.order or 0)
    ]
    return doc_dict


@frappe.whitelist(allow_guest=True)
def submit_survey_response(survey: str, department: str | None = None, answers: list | None = None):
    """Create Survey Response + Survey Answer docs for a public submission.

    `answers` should be a list of objects: { question: str, value: str, follow_up: str | null }.
    """  # noqa: E501
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
