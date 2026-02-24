from app.modules.analysis.recommender import generate_recommendations

def test_weak_topic_generates_recommendation():
    topic_scores = [{"percentage": 40.0, "name_en": "Fractions", "correct": 4, "total": 10}]
    section_scores = [{"correct": 4, "total_questions": 10}]
    time_analysis = {"skipped_count": 0, "avg_per_question": 60.0}
    
    recs = generate_recommendations(topic_scores, section_scores, time_analysis)
    assert len(recs) >= 2 # 1 for weak topic, 1 for <50% overall
    assert any("Fractions" in r for r in recs)

def test_no_recommendations_for_perfect_score():
    topic_scores = [{"percentage": 100.0, "name_en": "Fractions", "correct": 10, "total": 10}]
    section_scores = [{"correct": 10, "total_questions": 10}]
    time_analysis = {"skipped_count": 0, "avg_per_question": 40.0}
    
    recs = generate_recommendations(topic_scores, section_scores, time_analysis)
    assert len(recs) == 1
    assert "Excellent preparation!" in recs[0]

def test_max_5_recommendations_returned():
    topic_scores = [{"percentage": 0.0, "name_en": f"Topic {i}", "correct": 0, "total": 10} for i in range(10)]
    section_scores = [{"correct": 0, "total_questions": 100}]
    time_analysis = {"skipped_count": 50, "avg_per_question": 100.0}
    
    # Needs a lot of recommendations: 1 for skip, 1 for time, 10 for topics, 1 for overall <50% = 13 total 
    recs = generate_recommendations(topic_scores, section_scores, time_analysis)
    assert len(recs) == 5

def test_skipped_questions_generates_recommendation():
    topic_scores = [{"percentage": 80.0, "name_en": "Fractions", "correct": 8, "total": 10}]
    section_scores = [{"correct": 8, "total_questions": 20}] # 50% overall isn't terrible, but 12 skipped
    time_analysis = {"skipped_count": 12, "avg_per_question": 30.0}
    
    recs = generate_recommendations(topic_scores, section_scores, time_analysis)
    assert any("12 were left unanswered" in r for r in recs)

def test_slow_pace_generates_time_recommendation():
    topic_scores = [{"percentage": 80.0, "name_en": "Fractions", "correct": 8, "total": 10}]
    section_scores = [{"correct": 8, "total_questions": 10}]
    time_analysis = {"skipped_count": 0, "avg_per_question": 105.0} # way over 90s
    
    recs = generate_recommendations(topic_scores, section_scores, time_analysis)
    assert any("time management" in r for r in recs)
