from app.modules.analysis.schemas import ResponseData
from app.modules.analysis.scorer import (
    calculate_total_score,
    calculate_section_scores,
    calculate_topic_scores,
    calculate_time_analysis
)

def _make_response(selected, correct, marks=2, q_no=1, time=60, topic=1, sec=1, pct=None):
    return ResponseData(
        question_no=q_no,
        question_id=100 + q_no,
        selected_option=selected,
        correct_option=correct,
        topic_id=topic,
        topic_name_en=f"Topic {topic}",
        topic_name_mr=None,
        section_id=sec,
        section_label=f"Sec {sec}",
        subject_en=f"Subj {sec}",
        marks=marks,
        time_taken_seconds=time
    )

def test_all_correct_returns_perfect_score():
    responses = [_make_response(2, 2, marks=2, q_no=i) for i in range(1, 76)]
    result = calculate_total_score(responses)
    assert result["total_score"] == 150
    assert result["total_correct"] == 75
    assert result["total_wrong"] == 0
    assert result["total_skipped"] == 0
    assert result["percentage"] == 100.0
    assert result["grade"] == "Excellent"

def test_all_wrong_returns_0_score():
    responses = [_make_response(1, 2, marks=2, q_no=i) for i in range(1, 76)]
    result = calculate_total_score(responses)
    assert result["total_score"] == 0
    assert result["total_correct"] == 0
    assert result["total_wrong"] == 75
    assert result["percentage"] == 0.0
    assert result["grade"] == "Below Average"

def test_all_skipped_returns_0_score():
    responses = [_make_response(None, 2, marks=2, q_no=i) for i in range(1, 76)]
    result = calculate_total_score(responses)
    assert result["total_score"] == 0
    assert result["total_correct"] == 0
    assert result["total_wrong"] == 0
    assert result["total_skipped"] == 75
    assert result["percentage"] == 0.0

def test_grade_excellent_at_90_percent():
    # 90% of 150 is 135 (i.e. 67.5 questions correct, let's just do 10 total questions to test math)
    responses = [_make_response(2, 2, marks=2, q_no=i) for i in range(1, 10)] # 9 correct
    responses.append(_make_response(1, 2, marks=2, q_no=10)) # 1 wrong
    # 18/20 = 90%
    result = calculate_total_score(responses)
    assert result["percentage"] == 90.0
    assert result["grade"] == "Excellent"

def test_grade_below_average_at_49_percent():
    responses = [_make_response(2, 2, marks=2, q_no=i) for i in range(1, 5)] # 4 correct (8 marks)
    responses.extend(_make_response(1, 2, marks=2, q_no=i) for i in range(5, 11)) # 6 wrong
    # Total 10 questions, 8/20 marks = 40%
    result = calculate_total_score(responses)
    assert result["percentage"] == 40.0
    assert result["grade"] == "Below Average"

def test_section_scores_sum_to_total():
    responses = [
        _make_response(2, 2, sec=1, q_no=1), # correct sec 1
        _make_response(1, 2, sec=1, q_no=2), # wrong sec 1
        _make_response(3, 3, sec=2, q_no=3), # correct sec 2
    ]
    sections = calculate_section_scores(responses)
    assert len(sections) == 2
    assert sections[0]["section_id"] == 1
    assert sections[0]["correct"] == 1
    assert sections[0]["score"] == 2
    assert sections[0]["percentage"] == 50.0
    
    assert sections[1]["section_id"] == 2
    assert sections[1]["correct"] == 1
    assert sections[1]["score"] == 2
    assert sections[1]["percentage"] == 100.0

def test_topic_status_strong_at_70_percent():
    responses = [
        _make_response(2, 2, topic=1, q_no=1),
        _make_response(2, 2, topic=1, q_no=2),
        _make_response(2, 2, topic=1, q_no=3),
        _make_response(2, 2, topic=1, q_no=4),
        _make_response(1, 2, topic=1, q_no=5),
        _make_response(1, 2, topic=1, q_no=6),
        _make_response(1, 2, topic=1, q_no=7),
        _make_response(1, 2, topic=1, q_no=8),
        _make_response(1, 2, topic=1, q_no=9),
        _make_response(1, 2, topic=1, q_no=10),
    ]
    # Wait, 70% means 7 out of 10 must be correct.
    responses[:7] = [_make_response(2, 2, topic=1, q_no=i) for i in range(1, 8)]
    topics = calculate_topic_scores(responses)
    assert topics[0]["percentage"] == 70.0
    assert topics[0]["status"] == "strong"

def test_topic_status_weak_at_49_percent():
    responses = [_make_response(2, 2, topic=1, q_no=i) for i in range(1, 101)]
    # Make exactly 49 correct
    for i in range(49, 100):
        responses[i].selected_option = 1 # wrong
    topics = calculate_topic_scores(responses)
    assert topics[0]["percentage"] == 49.0
    assert topics[0]["status"] == "weak"

def test_time_analysis_finds_fastest_question():
    responses = [
        _make_response(2, 2, time=120, q_no=1),
        _make_response(2, 2, time=12, q_no=3),
        _make_response(2, 2, time=300, q_no=47),
    ]
    result = calculate_time_analysis(responses)
    assert result["fastest"]["question_no"] == 3
    assert result["fastest"]["seconds"] == 12
    assert result["slowest"]["question_no"] == 47
    assert result["slowest"]["seconds"] == 300
    assert result["total_time_seconds"] == 120 + 12 + 300
    assert result["avg_per_question"] == round((120 + 12 + 300) / 3, 2)
    assert 47 in result["overtime_questions"] # 300 > 144*2

def test_time_analysis_handles_null_times():
    responses = [
        _make_response(None, 2, time=None, q_no=1), # skipped and no time
        _make_response(1, 2, time=10, q_no=2),
    ]
    result = calculate_time_analysis(responses)
    assert result["skipped_count"] == 1
    assert result["total_time_seconds"] == 10
    assert result["avg_per_question"] == 5.0 # 10 / 2
    assert result["fastest"]["question_no"] == 2

def test_mixed_attempts_correct_percentage():
    responses = [
        _make_response(2, 2, marks=2, q_no=1), # correct
        _make_response(1, 2, marks=2, q_no=2), # wrong
        _make_response(None, 2, marks=2, q_no=3), # skipped
    ]
    result = calculate_total_score(responses)
    assert result["total_correct"] == 1
    assert result["total_wrong"] == 1
    assert result["total_skipped"] == 1
    assert result["total_score"] == 2
    assert result["percentage"] == round((2/6)*100, 2)
