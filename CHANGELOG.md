# Changelog

## OOP refactor
- Extracted CSV question loading and refresh/fallback behavior into `CsvQuestionRepository` and `QuestionBankService`.
- Extracted question-list/random-selection logic into `QuizService`.
- Extracted answer scoring and wrong-answer collection into `QuizScoringService`.
- Kept Flask route paths, template names, form fields, environment variable names, and API response shapes.
- Added unit tests and `docs/OOP_REFACTOR.md`.
