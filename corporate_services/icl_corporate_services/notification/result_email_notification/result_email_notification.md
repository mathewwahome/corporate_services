Dear {{ doc.employee_name }},

Thank you for completing: {{ doc.quiz }}

Your Results
----------------------------
Score:           {{ doc.score_ }}%
Correct Answers: {{ doc.correct_answers }} / {{ doc.total_questions }}
Result:          {{ doc.result }}
----------------------------

{% if doc.result == "Pending Review" %}
Your submission includes open-ended question(s) and is pending manual review. Final grading will be shared after review.
{% elif doc.passed %}
Congratulations! You have successfully passed this quiz.
{% else %}
You did not meet the passing score. Please review the material and try again.
{% endif %}

Regards,
HR Department
