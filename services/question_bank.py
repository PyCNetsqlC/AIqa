"""Question-bank loading and refresh services.

The classes in this module extract the existing CSV and refresh logic from the
Flask route module. CSV schema and fallback behavior are intentionally retained.
"""

import csv
import os
from typing import Any, Dict, Optional

from clawdatatodb import returnnal


class CsvQuestionRepository:
    """Loads the existing seven-column question CSV into the legacy dict shape."""

    def load(self, db_path: str) -> Dict[int, Dict[str, str]]:
        with open(db_path, mode="r", encoding="utf-8-sig", newline="") as file:
            csv_text = [row for row in csv.reader(file)]

        question_data: Dict[int, Dict[str, str]] = {}
        for index in range(1, len(csv_text)):
            question_data.update({
                index: {
                    csv_text[0][0]: csv_text[index][0],
                    csv_text[0][1]: csv_text[index][1],
                    csv_text[0][2]: csv_text[index][2],
                    csv_text[0][3]: csv_text[index][3],
                    csv_text[0][4]: csv_text[index][4],
                    csv_text[0][5]: csv_text[index][5],
                    csv_text[0][6]: csv_text[index][6],
                }
            })
        return question_data


class QuestionBankService:
    """Owns question-bank initialization, refresh, and fallback loading."""

    def __init__(self, repository: Optional[CsvQuestionRepository] = None):
        self.repository = repository or CsvQuestionRepository()
        self.questions: Optional[Dict[int, Dict[str, str]]] = None
        self.reload_job_times = 0

    @staticmethod
    def _environment_paths():
        return os.environ.get("MAIN_URL"), os.environ.get("DB"), os.environ.get("DB_2")

    def initialize(self) -> Dict[int, Dict[str, str]]:
        main_url, primary_db, backup_db = self._environment_paths()
        returnnal(main_url, primary_db)
        try:
            self.questions = self.repository.load(primary_db)
            if len(self.questions) == 0:
                returnnal(main_url, primary_db)
                self.questions = self.repository.load(primary_db)
                if len(self.questions) == 0:
                    self.questions = self.repository.load(backup_db)
                    raise ValueError("主資料庫內容為空，啟用備用資料庫")
        except Exception as error:
            print(f" 主要資料庫異常，改讀備用檔案... 詳細原因: {error}")
            try:
                self.questions = self.repository.load(backup_db)
                if len(self.questions) == 0:
                    raise ValueError("[AllDBCorruptionError] 主要資料庫損壞，且備用資料庫內容為空或內容資料格式錯誤！")
            except FileNotFoundError:
                raise ValueError("[AllDBCorruptionError] 主要資料庫損壞，且備用資料庫不存在！")
            except Exception as backup_error:
                raise RuntimeError(
                    "[AllDBCorruptionError] 主要與備用資料庫皆已毀損或無法讀取！"
                    f"原始錯誤: {backup_error}"
                )
        print("資料庫資料初始更新中,times應該要是零:0")
        return self.questions

    def refresh(self) -> Dict[int, Dict[str, str]]:
        main_url, primary_db, backup_db = self._environment_paths()
        returnnal(main_url, primary_db)
        try:
            self.questions = self.repository.load(primary_db)
            if len(self.questions) == 0:
                returnnal(main_url, primary_db)
                self.questions = self.repository.load(primary_db)
                if len(self.questions) == 0:
                    self.questions = self.repository.load(backup_db)
                    raise ValueError("主資料庫內容為空，啟用備用資料庫")
        except Exception as error:
            print(f" 主要資料庫異常，改讀備用檔案... 詳細原因: {error}")
            try:
                self.questions = self.repository.load(backup_db)
                if len(self.questions) == 0:
                    raise ValueError("[AllDBCorruptionError] 主要資料庫損壞，且備用資料庫內容為空或內容資料格式錯誤！")
            except FileNotFoundError:
                raise ValueError("[AllDBCorruptionError] 主要資料庫損壞，且備用資料庫不存在！")
            except Exception as backup_error:
                raise RuntimeError(
                    "[AllDBCorruptionError] 主要與備用資料庫皆已毀損或無法讀取！"
                    f"原始錯誤: {backup_error}"
                )
        self.reload_job_times += 1
        print(f"定時更新次數:{self.reload_job_times}", flush=True)
        return self.questions
