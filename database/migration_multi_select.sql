-- Add support for multi-selection questions
ALTER TABLE questions ADD COLUMN IF NOT EXISTS is_multi_select BOOLEAN DEFAULT false;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS correct_options SMALLINT[];
ALTER TABLE questions ALTER COLUMN correct_option DROP NOT NULL;

-- Add support for multiple selected options in responses
ALTER TABLE responses ADD COLUMN IF NOT EXISTS selected_options SMALLINT[];

-- Update v_exam_questions to include is_multi_select
DROP VIEW IF EXISTS v_exam_questions;
CREATE VIEW v_exam_questions AS
SELECT q.id,
    q.exam_id,
    q.section_id,
    q.topic_id,
    q.context_id,
    q.question_no,
    q.question_type,
    q.text_en,
    q.text_mr,
    q.question_image_url,
    q.question_image_alt_en,
    q.question_image_alt_mr,
    q.marks,
    q.difficulty,
    q.tags,
    q.is_multi_select,
    s.section_label,
    s.subject_en,
    s.subject_mr,
    t.name_en AS topic_name_en,
    t.name_mr AS topic_name_mr
FROM questions q
     LEFT JOIN sections s ON s.id = q.section_id
     LEFT JOIN topics t ON t.id = q.topic_id;

-- Update v_exam_answers to include correct_options and is_multi_select
DROP VIEW IF EXISTS v_exam_answers;
CREATE VIEW v_exam_answers AS
SELECT q.id AS question_id,
    q.exam_id,
    q.question_no,
    q.correct_option,
    q.correct_options,
    q.is_multi_select,
    q.explanation_en,
    q.explanation_mr,
    q.hint_en,
    q.hint_mr
FROM questions q;

-- Update trigger function to handle both single and multiple correct options
CREATE OR REPLACE FUNCTION sync_correct_option() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_multi_select THEN
        UPDATE options 
        SET is_correct = (option_no = ANY(NEW.correct_options))
        WHERE question_id = NEW.id;
    ELSE
        UPDATE options 
        SET is_correct = (option_no = NEW.correct_option)
        WHERE question_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
