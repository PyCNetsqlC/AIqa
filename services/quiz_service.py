"""Quiz selection and scoring logic extracted from Flask route handlers."""

import random
from typing import Dict, List, Any


class QuizService:
    def __init__(self, question_bank):
        self.question_bank = question_bank

    def all_questions(self) -> List[Dict[str, Any]]:
        all_data = []
        for index in range(1, len([self.question_bank][0]) + 1):
            [self.question_bank][0][index]["id"] = str(index)
            all_data.append(self.question_bank[index])
        return all_data

    def random_questions(self, requested_count) -> List[Dict[str, Any]]:
        n = 0
        i = 0
        random_num = set()
        random_qus = list()
        while n == 0:
            selected = random.randint(1, len(self.question_bank))
            if selected not in random_num:
                random_num.add(selected)
            elif selected in random_num:
                continue
            i += 1
            self.question_bank[selected]["id"] = str(i)
            random_qus.append(self.question_bank[selected])
            if len(random_num) == int(requested_count):
                break
        return random_qus


class QuizScoringService:
    """Keeps the original form-field names and score calculation behavior."""

    def score(self, form):
        score = 0
        number = form.get("number")
        average = 100 / int(number)
        correct_count = 0
        wrong_count = 0
        wrong_records = []

        for index in range(1, int(number) + 1):
            selected_answer = form.get(f"qus_{index}")
            correct_answer = form.get(f"ans_{index}")
            question_text = form.get(f"wrong_qus_{index}")
            if selected_answer[0] == correct_answer:
                score += average
                correct_count += 1
            else:
                wrong_count += 1
                wrong_records.append({
                    "id": index,
                    "wrong_qus": question_text,
                    "your_ans": selected_answer[0],
                    "correct_ans": correct_answer,
                })

        return {
            "score": score,
            "total": number,
            "correct": correct_count,
            "wrong": wrong_count,
            "wrong_records": wrong_records,
            "wrong_len": len(wrong_records),
        }
