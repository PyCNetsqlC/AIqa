"""Question-bank loading and refresh services.

The crawler updates the primary CSV file as a side effect. If crawling fails,
the service still attempts to use an existing primary CSV before falling back
 to the backup CSV.
"""

import csv
import os
from typing import Dict, Optional

from clawdatatodb import returnnal


class CsvQuestionRepository:
    """Load the existing seven-column question CSV into the legacy dict shape."""

    def load(self, db_path: str) -> Dict[int, Dict[str, str]]:
        if not db_path:
            raise ValueError("題庫路徑未設定")

        with open(db_path, mode="r", encoding="utf-8-sig", newline="") as file:
            csv_text = [row for row in csv.reader(file)]

        if not csv_text:
            return {}

        # Keep the original seven-column data shape while avoiding an IndexError
        # when a malformed CSV row has fewer columns than expected.
        headers = csv_text[0]
        question_data: Dict[int, Dict[str, str]] = {}
        for index, row in enumerate(csv_text[1:], start=1):
            if len(row) < 7 or len(headers) < 7:
                raise ValueError(f"CSV 第 {index + 1} 列欄位不足，預期至少 7 欄")
            question_data[index] = {headers[column]: row[column] for column in range(7)}
        return question_data


class QuestionBankService:
    """Own question-bank initialization, refresh, and fallback loading."""

    def __init__(self, repository: Optional[CsvQuestionRepository] = None):
        self.repository = repository or CsvQuestionRepository()
        self.questions: Optional[Dict[int, Dict[str, str]]] = None
        self.reload_job_times = 0

    @staticmethod
    def _environment_paths():
        return os.environ.get("MAIN_URL"), os.environ.get("DB"), os.environ.get("DB_2")

    def _load_questions(self) -> Dict[int, Dict[str, str]]:
        """Refresh the CSV snapshot, then load that snapshot for application use.

        ``returnnal`` performs crawling and writes the result to ``primary_db``.
        The application historically consumes the persisted CSV snapshot via the
        repository, so the crawler's returned list is intentionally not passed to
        ``repository.load`` (which expects a file path).
        """
        main_url, primary_db, backup_db = self._environment_paths()
        errors = []

        # Match the original startup flow: attempt a crawl before reading the
        # primary CSV snapshot. A crawl failure does not prevent loading an
        # already-existing snapshot.
        can_crawl = bool(main_url and primary_db)
        if can_crawl:
            try:
                returnnal(main_url, primary_db)
                print(f"主要題庫快照更新完成：{primary_db}", flush=True)
            except Exception as error:
                errors.append(f"主要題庫爬蟲更新失敗：{error}")
                print(errors[-1], flush=True)
        else:
            errors.append("MAIN_URL 或 DB 環境變數未設定，略過線上更新")
            print(errors[-1], flush=True)

        # Read the persisted primary snapshot. If it is empty, the legacy
        # behavior retries the crawler once and then reads the snapshot again.
        try:
            questions = self.repository.load(primary_db)
            if questions:
                return questions

            print("主要題庫快照內容為空，嘗試重新更新一次", flush=True)
            if can_crawl:
                try:
                    returnnal(main_url, primary_db)
                    print(f"主要題庫快照重新更新完成：{primary_db}", flush=True)
                except Exception as error:
                    errors.append(f"主要題庫第二次更新失敗：{error}")
                    print(errors[-1], flush=True)

            questions = self.repository.load(primary_db)
            if questions:
                return questions
            errors.append("主要題庫內容為空")
        except Exception as error:
            errors.append(f"主要題庫讀取失敗：{error}")
            print(errors[-1], flush=True)

        # Fallback to the backup CSV snapshot only after the primary snapshot
        # is missing, invalid, or empty.
        try:
            questions = self.repository.load(backup_db)
            if not questions:
                raise ValueError("備援題庫內容為空")
            print(f"已改用備援題庫：{backup_db}", flush=True)
            return questions
        except Exception as error:
            errors.append(f"備援題庫讀取失敗：{error}")
            self.questions = None
            raise RuntimeError(
                "[AllDBCorruptionError] 主要題庫與備援題庫皆無法載入。\n"
                + "\n".join(errors)
            ) from error

    def initialize(self) -> Dict[int, Dict[str, str]]:
        self.questions = self._load_questions()
        print("題庫初始化完成", flush=True)
        return self.questions

    def refresh(self) -> Dict[int, Dict[str, str]]:
        self.questions = self._load_questions()
        self.reload_job_times += 1
        print(f"定時更新次數:{self.reload_job_times}", flush=True)
        return self.questions
