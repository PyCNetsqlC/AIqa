"""Flask web/controller layer for AIqa.

Routes, templates, request field names, and response formats are retained while
business/data logic is delegated to service classes.
"""

import json
import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_apscheduler import APScheduler

from services.question_bank import QuestionBankService
from services.quiz_service import QuizService, QuizScoringService

load_dotenv()

app = Flask(__name__)
scheduler = APScheduler()
question_bank_service = QuestionBankService()
quiz_scoring_service = QuizScoringService()

# Keep the original module-level names available for compatibility.
time = 0
reload_job_times = 0
csv_dict = question_bank_service.initialize()
quiz_service = QuizService(csv_dict)


@scheduler.task('cron', id='reload_job', hour=9, minute=00, timezone='Asia/Taipei')
def reload_job():
    global csv_dict, quiz_service, reload_job_times
    csv_dict = question_bank_service.refresh()
    quiz_service = QuizService(csv_dict)
    reload_job_times = question_bank_service.reload_job_times


scheduler.init_app(app)
scheduler.start()


@app.route('/', methods=["GET", "POST"])
def index_get():
    global time
    time += 1
    class_list = ["All", "50", "25", "10"]
    if request.method == "POST":
        return render_template("testquestion_3.html")
    return render_template("index.html", class_list=class_list, time=time)


@app.route('/testquestion_3.html', methods=["GET", "POST"])
def index_post():
    class_list = ["All", "50", "25", "10"]
    if request.method == "POST":
        return_ob = request.form.get("Qusmodul-select")
        if return_ob == class_list[0]:
            url = os.environ.get("API_ONE")
            response_json = requests.get(url, verify=True).json()
            num = len(response_json)
        elif return_ob != class_list[0]:
            url = os.environ.get("API_TWO") + f"{return_ob}"
            response_json = requests.get(url, verify=True).json()
            num = len(response_json)
        else:
            return render_template("index.html", class_list=class_list, time=time)
        return render_template("testquestion_3.html", num=num, response_json=response_json)
    return """<h1>    !!! 檢測到異常操作  !!!<br>!!!  請回首頁進行正常操作 !!! </h1>"""


@app.route("/result.html", methods=["GET", "POST"])
def result():
    if request.method == "POST":
        result_data = quiz_scoring_service.score(request.form)
        return render_template("result.html", **result_data)
    return """<h1>    !!! 尚未進行作答  !!!<br>!!!  請回首頁進行測試 !!! </h1>"""


@app.route('/loaderio-be4fbf89bc160a080817c70bae94c7f0/')
def loaderio_verify():
    return "loaderio-be4fbf89bc160a080817c70bae94c7f0"


@app.route('/api/get_all', methods=["GET"])
def get_all():
    json_api = json.dumps(quiz_service.all_questions(), ensure_ascii=True, indent=4)
    return json_api


@app.route('/api/get_random', methods=["GET"])
def randm():
    requested_count = request.args.get('return_ob')
    json_api = json.dumps(quiz_service.random_questions(requested_count), ensure_ascii=True, indent=4)
    return json_api


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, use_reloader=False, port=8000)
