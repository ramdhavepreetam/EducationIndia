-- Support official answer-key cancelled questions.
-- Cancelled questions remain visible in review/admin views, but are excluded
-- from scoring totals by application logic.

ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS is_cancelled BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS cancelled_reason TEXT;

UPDATE questions
SET is_cancelled = false
WHERE is_cancelled IS NULL;

ALTER TABLE questions
    ALTER COLUMN is_cancelled SET NOT NULL;

CREATE OR REPLACE FUNCTION sync_correct_option() RETURNS TRIGGER AS $$
BEGIN
    IF COALESCE(NEW.is_cancelled, false) THEN
        UPDATE options
        SET is_correct = false
        WHERE question_id = NEW.id;
    ELSIF NEW.is_multi_select THEN
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

DROP TRIGGER IF EXISTS sync_correct_option_trigger ON questions;
CREATE TRIGGER sync_correct_option_trigger
AFTER INSERT OR UPDATE OF correct_option, correct_options, is_multi_select, is_cancelled
ON questions
FOR EACH ROW
EXECUTE FUNCTION sync_correct_option();
