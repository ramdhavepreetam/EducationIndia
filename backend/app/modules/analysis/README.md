# Analysis Module

Provides pure pure computation functions for scoring, topic analysis, time analysis, and recommendations. 
Wired into the attempt module to be triggered upon exam submission.

## Files
- `schemas.py`: `ResponseData` struct and `ReportSchema`.
- `scorer.py`: Pure functions to compute scores from list of `ResponseData`. Computes total_score, section_scores, topic_scores, and time_analysis.
- `recommender.py`: Pure function `generate_recommendations` to give strategic recommendations based on topic/section properties.
- `service.py`: Evaluator class orchestrating everything by loading raw data and formatting as response schemas.
- `router.py`: Only endpoint is `GET /api/analysis/attempts/{attempt_id}/report` which outputs precomputed JSONB stored in attempts table.

## Notes
- Pure functions; no direct DB writes or side effects.
- Analysis is synchronous and executed strictly on standard attempt submission edge transition.
