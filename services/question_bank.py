"""Question-bank loading and refresh services.

<<<<<<< HEAD
The crawler updates the primary CSV file as a side effect. If crawling fails,
the service still attempts to use an existing primary CSV before falling back
 to the backup CSV.
=======
The classes in this module extract the existing CSV and refresh logic from the
Flask route module. CSV schema and fallback behavior are intentionally retained.
>>>>>>> 01cb9de55b61b57460d578138990a42ebcef4319
"""

import csv
import os
from typing import Dict, Optional

from typing import Any, Dict, Optional

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

    """Own question-bank initialization, refresh, and fallback loading."""

    """Owns question-bank initialization, refresh, and fallback loading."""


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
