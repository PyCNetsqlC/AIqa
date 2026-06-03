from flask import Flask, render_template,request
import csv,requests,json,random
from flask_apscheduler import APScheduler
from datetime import datetime  
from clawdatatodb import returnnal

global time

time = 0

if time==0:
    returnnal()
    print(f"資料庫資料更新中,time:{time}")

with open("./db_file/clean.csv", mode="r", encoding="utf-8-sig",newline="") as f:
    csvfile = csv.reader(f)
    csv_text = [row for row in csvfile]
    csv_dict = dict()
        
    for i in range(1,len(csv_text)):
        csv_dict.update({i:{csv_text[0][0]:csv_text[i][0],
                    csv_text[0][1]:csv_text[i][1],
                    csv_text[0][2]:csv_text[i][2],
                    csv_text[0][3]:csv_text[i][3],
                    csv_text[0][4]:csv_text[i][4],
                    csv_text[0][5]:csv_text[i][5],
                    csv_text[0][6]:csv_text[i][6]}})



app = Flask(__name__)
scheduler = APScheduler()


'''mainpage'''

@app.route('/',methods=["GET","POST"])
def index():
    global time
    class_list = ["All","50","25","10"]
    time += 1
    if time==1:
        scheduler.add_job(
            id='startup_update_job',
            func=returnnal,
            trigger='date',
            run_date=datetime.now(),
            )

        scheduler.init_app(app)
        scheduler.start()
        print(f"資料庫資料更新中,time:{time}")

    if request.method=="POST":
        if request.form.get("Qusmodul-select") == class_list[0]:
'''
            url = "https://aiqa-1.onrender.com/api/get_all"
            response_json = requests.get(url,verify=False).json()
'''
            response_json = get_all()
            num = len(response_json)
        elif request.form.get("Qusmodul-select") == class_list[1]:
'''
            url = "https://aiqa-1.onrender.com/api/get_random_50"
            response_json =  requests.get(url,verify=False).json()
'''
            response_json = randm_50()
            num = len(response_json)
        elif request.form.get("Qusmodul-select") == class_list[2]:
'''
            url = "https://aiqa-1.onrender.com/api/get_random_25"
            response_json = requests.get(url,verify=False).json()
'''
            response_json = randm_25()
            num = len(response_json)
        elif request.form.get("Qusmodul-select") == class_list[3]:
'''
            url = "https://aiqa-1.onrender.com/api/get_random_10"
            response_json = requests.get(url,verify=False).json()
'''
            response_json = randm_10()
            num = len(response_json)
        else:
            return render_template("index.html",class_list=class_list)
        
        return render_template("testquestion.html",num=num,response_json=response_json)
    
    return render_template("index.html",class_list=class_list)



@app.route("/testquestion.html", methods=["GET", "POST"])
def testquestion():
    sorce = 0  # 你的總分變數

    if request.method == "POST":
        num = request.form.get("number")
        avgcen = 100 / int(num)

        # 💡 新增：用來統計數量與收集錯題的變數
        correct_count = 0
        wrong_count = 0
        wrong_records = []  # 專門裝寫錯的題目

        for i in range(1, int(num) + 1):
            tyy = request.form.get(f"qus_{i}")  # 使用者選的答案
            cta = request.form.get(f"ans_{i}")  # 隱藏的正確答案

            # 進行數值驗證
            if tyy == cta:
                sorce += avgcen
                correct_count += 1  # 答對加 1 題
            else:
                wrong_count += 1  # 答錯加 1 題
                # 💡 核心新增：只要答錯，就把這題的編號、作答、正解記下來
                wrong_records.append(
                    {"id": i, "your_ans": tyy, "correct_ans": cta}
                )

        # 💡 核心修正：計算完畢後，將所有數據 return 給 result.html 網頁
        return render_template(
            "result.html",
            score=sorce,  # 四捨五入成整數分數
            total=num,  # 總題數
            correct=correct_count,  # 答對題數
            wrong=wrong_count,  # 答錯題數
            wrong_records=wrong_records,  # 錯題名單
            wrong_len = len(wrong_records),
        )

    # 💡 提示：這裡記得放你原本 GET 請求時的抽題與 return 邏輯
    # return render_template("testquestion.html", num=..., response_json=...)



'''API'''
#all_qus
@app.route('/api/get_all',methods=["GET"])
def get_all():
    all_data = []
    for i in range(1,len([csv_dict][0])+1):
        ［csv_dict][0][i]["id"] = str(i)
        all_data.append([csv_dict][0][i])
    #json_api = json.dumps(all_data, ensure_ascii=True, indent=4)
    return all_data



#random_qus_10
@app.route('/api/get_random_10',methods=["GET"])
def randm_10():
    n = 0
    i=0
    random_num = set()
    random_qus = list()
    while n==0:
        f = random.randint(1,len(csv_dict))
        if f not in random_num:
            random_num.add(f)
        elif f in random_num:
            continue
        i+=1
        csv_dict[f]["id"] = str(i)
        random_qus.append(csv_dict[f])
        if len(random_num)==10:
            break
    #json_api = json.dumps(random_qus, ensure_ascii=True, indent=4)
    return random_qus


#random_qus_25
@app.route('/api/get_random_25',methods=["GET"])
def randm_25():
    n = 0
    i=0
    random_num = set()
    random_qus = list()
    while n==0:
        f = random.randint(1,len(csv_dict))
        if f not in random_num:
            random_num.add(f)
        elif f in random_num:
            continue
        i+=1
        csv_dict[f]["id"] = str(i)
        random_qus.append(csv_dict[f])
        if len(random_num)==25:
            break
    #json_api = json.dumps(random_qus, ensure_ascii=True, indent=4)
    return random_qus


#random_qus_50
@app.route('/api/get_random_50',methods=["GET"])
def randm_50():
    n = 0
    i=0
    random_num = set()
    random_qus = list()
    while n==0:
        f = random.randint(1,len(csv_dict))
        if f not in random_num:
            random_num.add(f)
        elif f in random_num:
            continue
        i+=1
        csv_dict[f]["id"] = str(i)
        random_qus.append(csv_dict[f])
        if len(random_num)==50:
            break
    #json_api = json.dumps(random_qus, ensure_ascii=True, indent=4)
    return random_qus


if __name__ == "__main__":
    # 設定定時排程（範例：每天台灣中午 12 點執行 = UTC 4 點）
    app.run(host='0.0.0.0',debug=True, use_reloader=False, port=8000)





