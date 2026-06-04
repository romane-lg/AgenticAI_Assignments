import json
from pathlib import Path
from typing import Any, Literal

from agents import function_tool
from pydantic import BaseModel


DATA_DIR = Path(__file__).parent / "data"


def _load_json(filename: str) -> dict[str, Any]:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


class CourseRecommendation(BaseModel):
    searching_for_course: str
    matched_course_id: str | None
    matched_course_title: str | None
    prerequisite_passed: Literal["yes", "no"]
    message: str
    missing_prerequisites: list[str]


class AdvisorResponse(BaseModel):
    answer: str
    course_ids: list[str]
    approval_status: Literal[
        "approved",
        "blocked",
        "informational",
        "out_of_scope",
        "needs_advisor",
    ]
    advisor_approval_required: bool
    guardrail_triggered: str | None
    approved_course_id: str | None
    state_notes: list[str]


class GuardrailDecision(BaseModel):
    guardrail_name: str
    blocked: bool
    message: str


class CreditLoadReview(BaseModel):
    course_ids: list[str]
    total_credits: int
    max_credits_without_approval: int
    advisor_approval_required: bool
    missing_course_ids: list[str]
    message: str


class CreditProgressReview(BaseModel):
    completed_credits: int
    planned_course_ids: list[str]
    planned_credits: int
    projected_credits: int
    credits_required_to_graduate: int
    credits_left_to_graduate: int
    missing_course_ids: list[str]
    message: str


def _search_course_data(query: str) -> list[dict[str, Any]]:
    catalog = _load_json("course_catalog.json")
    normalized_query = query.strip().lower()

    if not normalized_query:
        return []

    matches = []
    for course in catalog["courses"]:
        searchable_text = " ".join(
            [
                course["course_id"],
                course["title"],
                course["department"],
                str(course["level"]),
                f"{course['level']} level",
                *course.get("tags", []),
            ]
        ).lower()

        if normalized_query in searchable_text:
            matches.append(course)

    return matches


def _review_credit_load_data(course_ids: list[str]) -> dict[str, Any]:
    catalog = _load_json("course_catalog.json")
    student = _load_json("student_profile.json")
    normalized_course_ids = [course_id.strip().upper() for course_id in course_ids]
    course_by_id = {course["course_id"]: course for course in catalog["courses"]}

    matched_courses = [
        course_by_id[course_id]
        for course_id in normalized_course_ids
        if course_id in course_by_id
    ]
    missing_course_ids = [
        course_id for course_id in normalized_course_ids if course_id not in course_by_id
    ]
    total_credits = sum(course["credits"] for course in matched_courses)
    max_credits = student["constraints"]["max_credits_allowed_without_approval"]
    advisor_approval_required = total_credits > max_credits

    if missing_course_ids:
        message = (
            "Some requested courses were not found in the catalog: "
            f"{', '.join(missing_course_ids)}."
        )
    elif advisor_approval_required:
        message = (
            f"The selected schedule has {total_credits} credits, which is above "
            f"the {max_credits}-credit limit. A human advisor must approve this "
            "course load before it can be recommended."
        )
    else:
        message = (
            f"The selected schedule has {total_credits} credits, which is within "
            f"the {max_credits}-credit limit."
        )

    return CreditLoadReview(
        course_ids=[course["course_id"] for course in matched_courses],
        total_credits=total_credits,
        max_credits_without_approval=max_credits,
        advisor_approval_required=advisor_approval_required,
        missing_course_ids=missing_course_ids,
        message=message,
    ).model_dump()


def _calculate_credit_progress_data(
    planned_course_ids: list[str] | None = None,
) -> dict[str, Any]:
    catalog = _load_json("course_catalog.json")
    student = _load_json("student_profile.json")
    credit_database = _load_json("student_credit_database.json")

    normalized_planned_ids = [
        course_id.strip().upper() for course_id in planned_course_ids or []
    ]
    course_by_id = {course["course_id"]: course for course in catalog["courses"]}
    completed_course_ids = {
        course["course_id"] for course in student["completed_courses"]
    }
    planned_courses = [
        course_by_id[course_id]
        for course_id in normalized_planned_ids
        if course_id in course_by_id and course_id not in completed_course_ids
    ]
    missing_course_ids = [
        course_id for course_id in normalized_planned_ids if course_id not in course_by_id
    ]
    completed_credits = sum(course["credits"] for course in student["completed_courses"])
    planned_credits = sum(course["credits"] for course in planned_courses)

    student_credit_record = next(
        (
            record
            for record in credit_database["students"]
            if record["student_id"] == student["student_id"]
        ),
        None,
    )
    credits_required = (
        student_credit_record["credits_required_to_graduate"]
        if student_credit_record
        else 120
    )
    projected_credits = completed_credits + planned_credits
    credits_left = max(credits_required - projected_credits, 0)

    if missing_course_ids:
        message = (
            "Some planned courses were not found in the catalog: "
            f"{', '.join(missing_course_ids)}."
        )
    elif planned_courses:
        message = (
            f"With {planned_credits} planned credits, the student would have "
            f"{projected_credits} completed or planned credits and "
            f"{credits_left} credits left to graduate."
        )
    else:
        message = (
            f"The student currently has {completed_credits} completed credits "
            f"and {credits_left} credits left to graduate."
        )

    return CreditProgressReview(
        completed_credits=completed_credits,
        planned_course_ids=[course["course_id"] for course in planned_courses],
        planned_credits=planned_credits,
        projected_credits=projected_credits,
        credits_required_to_graduate=credits_required,
        credits_left_to_graduate=credits_left,
        missing_course_ids=missing_course_ids,
        message=message,
    ).model_dump()


def _check_prerequisite_data(
    course_id: str,
    additional_completed_courses: list[str] | None = None,
) -> dict[str, Any]:
    prerequisites = _load_json("prerequisites.json")["rules"]
    student = _load_json("student_profile.json")

    normalized_course_id = course_id.strip().upper()
    completed = {course["course_id"] for course in student["completed_courses"]}
    completed.update(
        course.strip().upper() for course in additional_completed_courses or []
    )
    in_progress_courses = {
        course["course_id"]
        for course in student.get("current_enrollments", [])
        if course.get("status") == "enrolled"
    }

    rule = next(
        (item for item in prerequisites if item["course_id"] == normalized_course_id),
        None,
    )

    if rule is None:
        return {
            "course_id": normalized_course_id,
            "eligible": False,
            "requires_advisor_review": True,
            "missing_prerequisites": [],
            "in_progress_prerequisites": [],
            "message": "No prerequisite rule found for this course.",
        }

    missing_prerequisites = []
    in_progress_prerequisites = []
    completed_prerequisites = []

    for requirement in rule.get("prerequisites", []):
        courses = requirement["courses"]

        if requirement["type"] == "all_of":
            completed_prerequisites.extend(item for item in courses if item in completed)
            missing = [item for item in courses if item not in completed]
            in_progress = [item for item in missing if item in in_progress_courses]
            missing_prerequisites.extend(
                item for item in missing if item not in in_progress
            )
            in_progress_prerequisites.extend(in_progress)

        if requirement["type"] == "one_of":
            has_completed_option = any(item in completed for item in courses)
            has_in_progress_option = any(item in in_progress_courses for item in courses)
            completed_prerequisites.extend(item for item in courses if item in completed)

            if not has_completed_option and has_in_progress_option:
                in_progress_prerequisites.append("one of: " + ", ".join(courses))
            elif not has_completed_option:
                missing_prerequisites.append("one of: " + ", ".join(courses))

    eligible = not missing_prerequisites and not in_progress_prerequisites

    return {
        "course_id": normalized_course_id,
        "eligible": eligible,
        "requires_advisor_review": bool(missing_prerequisites),
        "completed_prerequisites": completed_prerequisites,
        "missing_prerequisites": missing_prerequisites,
        "in_progress_prerequisites": in_progress_prerequisites,
        "prerequisite_rule": rule,
        "message": (
            "Student satisfies prerequisites."
            if eligible
            else "Student does not fully satisfy prerequisites."
        ),
    }


def build_course_recommendation(
    course_query: str,
    additional_completed_courses: list[str] | None = None,
) -> CourseRecommendation:
    matches = _search_course_data(course_query)

    if not matches:
        return CourseRecommendation(
            searching_for_course=course_query,
            matched_course_id=None,
            matched_course_title=None,
            prerequisite_passed="no",
            message=f"No course found for '{course_query}'.",
            missing_prerequisites=[],
        )

    course = matches[0]
    prerequisite_result = _check_prerequisite_data(
        course["course_id"],
        additional_completed_courses=additional_completed_courses,
    )
    missing = prerequisite_result["missing_prerequisites"]
    in_progress = prerequisite_result["in_progress_prerequisites"]
    all_missing = missing + in_progress

    if prerequisite_result["eligible"]:
        message = f"Prerequisite passed: yes. You can take {course['course_id']}."
        prerequisite_passed = "yes"
    else:
        needed = ", ".join(all_missing)
        message = (
            f"Prerequisite passed: no. You need to take the course {needed} "
            f"in order to take the course {course['course_id']}."
        )
        prerequisite_passed = "no"

    return CourseRecommendation(
        searching_for_course=course_query,
        matched_course_id=course["course_id"],
        matched_course_title=course["title"],
        prerequisite_passed=prerequisite_passed,
        message=message,
        missing_prerequisites=all_missing,
    )


def enforce_prerequisite_block(
    recommendation: CourseRecommendation,
) -> GuardrailDecision:
    if recommendation.prerequisite_passed == "yes":
        return GuardrailDecision(
            guardrail_name="BLOCK_MISSING_PREREQUISITE_APPROVAL",
            blocked=False,
            message="Approval allowed because prerequisites are satisfied.",
        )

    return GuardrailDecision(
        guardrail_name="BLOCK_MISSING_PREREQUISITE_APPROVAL",
        blocked=True,
        message=(
            "Approval blocked: the student cannot be approved for "
            f"{recommendation.matched_course_id} because they are missing "
            f"{', '.join(recommendation.missing_prerequisites)}."
        ),
    )


def enforce_course_scope(user_message: str) -> GuardrailDecision:
    course_keywords = [
        "course",
        "class",
        "prerequisite",
        "prereq",
        "credit",
        "catalog",
        "level",
        "take",
        "graduate",
        "advisor",
        "advising",
        "comp",
        "math",
        "stat",
        "econ",
    ]
    normalized_message = user_message.lower()
    is_course_related = any(
        keyword in normalized_message for keyword in course_keywords
    )

    if is_course_related:
        return GuardrailDecision(
            guardrail_name="BLOCK_NON_COURSE_ADVISING_REQUEST",
            blocked=False,
            message="Request is within course advising scope.",
        )

    return GuardrailDecision(
        guardrail_name="BLOCK_NON_COURSE_ADVISING_REQUEST",
        blocked=True,
        message=(
            "Sorry I am a course advising agent, "
            "I am unable to fulffil your request"
        ),
    )


@function_tool
def search_course(query: str) -> list[dict[str, Any]]:
    """Search the course catalog by course id, title, department, or tag."""
    return _search_course_data(query)


@function_tool
def check_prerequisite(
    course_id: str,
    additional_completed_courses: list[str] | None = None,
) -> dict[str, Any]:
    """Check whether the fixture student satisfies prerequisites for a course."""
    return _check_prerequisite_data(
        course_id,
        additional_completed_courses=additional_completed_courses,
    )


@function_tool
def review_credit_load(course_ids: list[str]) -> dict[str, Any]:
    """Check whether a proposed term schedule exceeds the credit load limit."""
    return _review_credit_load_data(course_ids)


@function_tool
def calculate_credit_progress(
    planned_course_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Calculate projected credits completed and credits left to graduate."""
    return _calculate_credit_progress_data(planned_course_ids=planned_course_ids)
