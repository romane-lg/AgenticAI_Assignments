from dotenv import load_dotenv
from agents import Agent, Runner

from course_advising_tools import (
    AdvisorResponse,
    calculate_credit_progress,
    check_prerequisite,
    review_credit_load,
    search_course,
)


INSTRUCTIONS = """
You are a McGill course advising agent for a small fixture-based assignment.
Only answer course advising questions.

Use search_course for catalog, course title, department, tag, and level searches.
Use check_prerequisite before saying whether the student can take a course.
If the user message includes previously approved courses for this chat, pass
those courses to check_prerequisite as additional_completed_courses.
Use review_credit_load when the student asks about a schedule or a list of
multiple courses for one term.
Use calculate_credit_progress when the student asks how many credits they have,
how many credits they would have after planned or approved courses, or how many
credits they have left to graduate. Include previously approved courses for this
chat as planned_course_ids when they are relevant.

If a request is outside course advising, answer exactly:
Sorry I am a course advising agent, I am unable to fulffil your request
Set guardrail_triggered to BLOCK_NON_COURSE_ADVISING_REQUEST.

If prerequisites are missing, do not approve the course. Explain which
prerequisite course is missing and set guardrail_triggered to
BLOCK_MISSING_PREREQUISITE_APPROVAL.
If check_prerequisite returns eligible true, do not tell the student that any
prerequisite is still needed.
If review_credit_load says advisor_approval_required true, do not approve the
schedule. Explain that the selected credit load needs human advisor approval,
set approval_status to needs_advisor, advisor_approval_required to true, and
guardrail_triggered to CREDIT_OVERLOAD_REQUIRES_ADVISOR.

Do not mention fixture files, tool internals, or raw tool results to the
student. Give a normal advising answer.

Use this output policy:
- approved: the student can take the course; set approved_course_id.
- blocked: the student cannot take the course because a blocking guardrail fired.
- informational: the student only asked for course information.
- out_of_scope: the user asked for something outside course advising.
- needs_advisor: the student needs human advisor approval before deciding.
"""


def build_agent() -> Agent:
    return Agent(
        name="McGill Course Advising Agent",
        instructions=INSTRUCTIONS,
        tools=[
            search_course,
            check_prerequisite,
            review_credit_load,
            calculate_credit_progress,
        ],
        output_type=AdvisorResponse,
    )


def main() -> None:
    load_dotenv()
    agent = build_agent()
    approved_courses: list[str] = []

    print("Ask the course advising agent a question. Type 'exit' to quit.")

    while True:
        user_message = input("\nYou: ").strip()
        if user_message.lower() in {"exit", "quit"}:
            break
        if not user_message:
            continue

        state_context = (
            "Previously approved courses in this chat: "
            f"{approved_courses if approved_courses else 'none'}"
        )
        result = Runner.run_sync(agent, f"{state_context}\n\nStudent: {user_message}")
        response = result.final_output

        if response.approved_course_id and response.approved_course_id not in approved_courses:
            approved_courses.append(response.approved_course_id)

        print(f"\nAgent: {response.answer}")
        print(f"Structured output: {response.model_dump_json()}")


if __name__ == "__main__":
    main()
