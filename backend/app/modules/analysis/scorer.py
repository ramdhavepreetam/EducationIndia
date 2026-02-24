"""
Pure functions for score computation. No database access.
"""
from typing import List, Dict, Any
from app.modules.analysis.schemas import ResponseData

def calculate_total_score(responses: List[ResponseData]) -> Dict[str, Any]:
    total_score = 0
    total_correct = 0
    total_wrong = 0
    total_skipped = 0
    total_possible_marks = 0

    for r in responses:
        total_possible_marks += r.marks
        if r.selected_option is None:
            total_skipped += 1
        elif r.selected_option == r.correct_option:
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

        if r.selected_option is not None and r.selected_option == r.correct_option:
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
        
        if r.selected_option is not None and r.selected_option == r.correct_option:
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
        if r.selected_option is None:
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
