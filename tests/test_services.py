import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.question_bank import CsvQuestionRepository
from services.quiz_service import QuizScoringService, QuizService


class CsvQuestionRepositoryTests(unittest.TestCase):
    def test_loads_existing_seven_column_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "questions.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["id", "question", "options_1", "options_2", "options_3", "options_4", "correct_answer"])
                writer.writerow(["1", "Question?", "A", "B", "C", "D", "A"])
            result = CsvQuestionRepository().load(str(path))
        self.assertEqual(result[1]["question"], "Question?")
        self.assertEqual(result[1]["correct_answer"], "A")


class QuizServiceTests(unittest.TestCase):
    def test_all_questions_keeps_flat_list_response_shape(self):
        questions = {1: {"id": "1", "question": "Q1"}, 2: {"id": "2", "question": "Q2"}}
        result = QuizService(questions).all_questions()
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0]["id"], "1")

    @patch("services.quiz_service.random.randint", side_effect=[1, 2])
    def test_random_questions_returns_requested_count(self, _randint):
        questions = {1: {"question": "Q1"}, 2: {"question": "Q2"}}
        result = QuizService(questions).random_questions("2")
        self.assertEqual(len(result), 2)
        self.assertEqual([item["id"] for item in result], ["1", "2"])


class QuizScoringServiceTests(unittest.TestCase):
    def test_scores_answers_and_collects_wrong_answers(self):
        form = {
            "number": "2",
            "qus_1": "A", "ans_1": "A", "wrong_qus_1": "Question 1",
            "qus_2": "B", "ans_2": "C", "wrong_qus_2": "Question 2",
        }
        result = QuizScoringService().score(form)
        self.assertEqual(result["score"], 50.0)
        self.assertEqual(result["correct"], 1)
        self.assertEqual(result["wrong"], 1)
        self.assertEqual(result["wrong_records"][0]["correct_ans"], "C")


if __name__ == "__main__":
    unittest.main()
