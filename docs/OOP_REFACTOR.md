# AIqa OOP 重構說明

## 重構原則

本次以「不刻意改變既有功能」為原則，保留既有 Flask 路由、HTTP 方法、模板名稱、表單欄位、API JSON 回應格式、環境變數名稱、CSV 欄位順序、排程時間與題庫備援流程。主要變動是將資料存取、題庫生命週期、抽題與計分邏輯從路由層抽離成類別。

## 新的責任分工

- `app.py`：Flask 應用程式、路由、HTTP 請求／回應及排程掛接。
- `services/question_bank.py`
  - `CsvQuestionRepository`：讀取既有 CSV，回傳原本以整數索引、欄位名稱為鍵的字典結構。
  - `QuestionBankService`：執行啟動載入、定時更新、主要／備用 CSV 的既有回退流程。
- `services/quiz_service.py`
  - `QuizService`：提供全部題目與隨機抽題資料。
  - `QuizScoringService`：計算分數、答對／答錯數及錯題紀錄。
- `tests/test_services.py`：對資料讀取、題目回應形狀、隨機抽題與計分服務進行單元測試。

## 相容性保留

以下路由與原路徑一致：

- `GET/POST /`
- `GET/POST /testquestion_3.html`
- `GET/POST /result.html`
- `GET /loaderio-be4fbf89bc160a080817c70bae94c7f0/`
- `GET /api/get_all`
- `GET /api/get_random?return_ob=...`

原本的 `templates/`、`db_file/`、`clawdatatodb.py` 及相依套件清單均予以保留。`app:app` 仍是 Flask WSGI 入口。

## 刻意沒有在本次處理的問題

為遵守功能不變的要求，本次沒有擅自更改既有抽題參數邊界、答題表單驗證、外部 API 逾時策略、爬蟲 TLS 驗證設定、資料更新交易方式或部署 worker／排程策略。這些可能值得另開變更，但應另行定義需求與回歸測試，不混入本次 OOP 重構。

## 本地檢查

執行：

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py clawdatatodb.py services tests
```

正式啟動前仍需依部署環境設定 `MAIN_URL`、`DB`、`DB_2`、`API_ONE`、`API_TWO`，並安裝 `requirements.txt` 中的相依套件。
