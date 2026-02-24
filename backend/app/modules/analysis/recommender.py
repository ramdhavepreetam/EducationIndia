from typing import List, Dict, Any

def generate_recommendations(
    topic_scores: List[Dict[str, Any]],
    section_scores: List[Dict[str, Any]],
    time_analysis: Dict[str, Any]
) -> List[str]:
    """
    Generate strategic recommendations based on performance.
    Maximum 5 recommendations returned (most important first).
    """
    recs = []
    
    # Check skipped count
    skipped = time_analysis.get("skipped_count", 0)
    if skipped > 10:
        recs.append(f"Try to attempt all questions — {skipped} were left unanswered.")
        
    # Check time management
    avg = time_analysis.get("avg_per_question", 0.0)
    if avg > 90:
        recs.append(f"Work on time management — average {avg}s per question, target under 72s.")
        
    # Check weak topics
    weak_topics = [t for t in topic_scores if t.get("percentage", 0) < 50.0]
    for topic in weak_topics:
        recs.append(
            f"Practice more {topic['name_en']} — you scored {topic['percentage']}% "
            f"({topic['correct']}/{topic['total']} correct)."
        )
        
    # Check overall percentage
    total_correct = sum(s.get("correct", 0) for s in section_scores)
    total_questions = sum(s.get("total_questions", 0) for s in section_scores)
    
    overall_pct = (total_correct / total_questions * 100) if total_questions > 0 else 0.0
    if overall_pct < 50.0:
        recs.append("Attempt previous year papers regularly to build speed and accuracy.")
        
    # If perfect score / strong topics
    if not weak_topics and overall_pct >= 70.0:
        recs.append("Excellent preparation! Focus on maintaining accuracy under timed conditions.")

    return recs[:5]
