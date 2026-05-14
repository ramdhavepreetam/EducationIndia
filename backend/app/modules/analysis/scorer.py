"""
Pure functions for score computation. No database access.
"""
from typing import List, Dict, Any, Optional
from app.modules.analysis.schemas import ResponseData


def _is_correct(r: ResponseData) -> bool:
    """
    Determine if a response is correct.
    - Multi-select question (is_multi_select=True):
      selected_options must exactly match correct_options (order doesn't matter).
    - Multi-answer fallback (correct_options set, is_multi_select=False):
      selected_option must be IN the list (either/or).
    - Single-answer (correct_option set): exact equality.
    """
    # 1. Handle strict multi-select (Select Two)
    if getattr(r, 'is_multi_select', False):
        if not r.selected_options or not r.correct_options:
            return False
        return set(r.selected_options) == set(r.correct_options)

    # 2. Handle simple selected option
    if r.selected_option is None:
        return False
        
    # Either/Or logic (fallback for 5th grade or legacy)
    if r.correct_options:
        return r.selected_option in r.correct_options
        
    # Standard single answer
    if r.correct_option is not None:
        return r.selected_option == r.correct_option
        
    return False


def _is_answered(r: ResponseData) -> bool:
    """A response is answered if it has a single option or any multi-select options."""
    if getattr(r, "is_multi_select", False):
        return bool(r.selected_options)
    return r.selected_option is not None


def calculate_total_score(responses: List[ResponseData]) -> Dict[str, Any]:
    total_score = 0
    total_correct = 0
    total_wrong = 0
    total_skipped = 0
    total_possible_marks = 0

    for r in responses:
        total_possible_marks += r.marks
        if not _is_answered(r):
            total_skipped += 1
        elif _is_correct(r):
            total_correct += 1
            total_score += r.marks
        else:
            total_wrong += 1
    
    percentage = round((total_score / total_possible_marks * 100), 2) if total_possible_marks > 0 else 0.0
    
    if percentage >= 90:
        grade = "Excellent"
    elif percentage >= 70:
        grade = "Good"
    elif percentage >= 50:
        grade = "Average"
    else:
        grade = "Below Average"

    return {
        "total_score": total_score,
        "total_correct": total_correct,
        "total_wrong": total_wrong,
        "total_skipped": total_skipped,
        "percentage": percentage,
        "grade": grade,
    }

def calculate_section_scores(responses: List[ResponseData]) -> List[Dict[str, Any]]:
    # Map section_id to metrics
    sections: Dict[int, Dict[str, Any]] = {}

    for r in responses:
        if r.section_id not in sections:
            sections[r.section_id] = {
                "section_id": r.section_id,
                "label": r.section_label,
                "subject_en": r.subject_en,
                "subject_mr": getattr(r, "subject_mr", None),
                "correct": 0,
                "total_questions": 0,
                "score": 0,
                "total_marks": 0,
                "percentage": 0.0,
            }
        
        sec = sections[r.section_id]
        sec["total_questions"] += 1
        sec["total_marks"] += r.marks

        if _is_answered(r) and _is_correct(r):
            sec["correct"] += 1
            sec["score"] += r.marks
            
    # Compute percentages
    result = []
    # sort by section_id typically or assume they preserve order
    for s_id in sorted(sections.keys()):
        sec = sections[s_id]
        sec["percentage"] = round((sec["score"] / sec["total_marks"] * 100), 2) if sec["total_marks"] > 0 else 0.0
        result.append(sec)
        
    return result

def calculate_topic_scores(responses: List[ResponseData]) -> List[Dict[str, Any]]:
    topics: Dict[int, Dict[str, Any]] = {}
    
    for r in responses:
        if r.topic_id not in topics:
            topics[r.topic_id] = {
                "topic_id": r.topic_id,
                "name_en": r.topic_name_en,
                "name_mr": r.topic_name_mr,
                "correct": 0,
                "total": 0,
                "percentage": 0.0,
                "status": "weak"
            }
        
        top = topics[r.topic_id]
        top["total"] += 1
        
        if _is_answered(r) and _is_correct(r):
            top["correct"] += 1

    result = []
    for t_id in sorted(topics.keys()):
        top = topics[t_id]
        pct = round((top["correct"] / top["total"] * 100), 2) if top["total"] > 0 else 0.0
        top["percentage"] = pct
        
        if pct >= 70:
            top["status"] = "strong"
        elif pct >= 50:
            top["status"] = "average"
        else:
            top["status"] = "weak"
            
        result.append(top)
        
    return result

def calculate_time_analysis(responses: List[ResponseData]) -> Dict[str, Any]:
    total_time_seconds = 0
    skipped_count = 0
    valid_times = []
    
    for r in responses:
        if not _is_answered(r):
            skipped_count += 1
        if r.time_taken_seconds is not None:
            total_time_seconds += r.time_taken_seconds
            valid_times.append((r.time_taken_seconds, r.question_no))
            
    total_questions = len(responses)
    avg_per_question = round((total_time_seconds / total_questions), 2) if total_questions > 0 else 0.0
    
    fastest = None
    slowest = None
    overtime_questions = [] # time > 2x average
    
    if valid_times:
        valid_times.sort(key=lambda x: x[0])
        fast_t, fast_q = valid_times[0]
        slow_t, slow_q = valid_times[-1]
        
        fastest = {"question_no": fast_q, "seconds": fast_t}
        slowest = {"question_no": slow_q, "seconds": slow_t}
        
        overtime_threshold = avg_per_question * 2
        for t, q in valid_times:
            if t > overtime_threshold and overtime_threshold > 0:
                overtime_questions.append(q)
                
    return {
        "total_time_seconds": total_time_seconds,
        "avg_per_question": avg_per_question,
        "fastest": fastest,
        "slowest": slowest,
        "skipped_count": skipped_count,
        "overtime_questions": overtime_questions
    }
