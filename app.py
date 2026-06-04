from flask import Flask, render_template,request
import csv,requests,json,random,os
from dotenv import load_dotenv
from flask_apscheduler import APScheduler
from clawdatatodb import returnnal

global time
global return_ob
global csv_dict

load_dotenv()

#資料庫載入函式
def db_reload(DB):
    with open(DB, mode="r", encoding="utf-8-sig",newline="") as f:
        csvfile = csv.reader(f)
        csv_text = [row for row in csvfile]
        _csv_dict = dict()
        for i in range(1,len(csv_text)):
            _csv_dict.update({i:{csv_text[0][0]:csv_text[i][0],
                        csv_text[0][1]:csv_text[i][1],
                        csv_text[0][2]:csv_text[i][2],
                        csv_text[0][3]:csv_text[i][3],
                        csv_text[0][4]:csv_text[i][4],
                        csv_text[0][5]:csv_text[i][5],
                        csv_text[0][6]:csv_text[i][6]}})
        return _csv_dict
    


#內部自我喚醒區塊
'''待建置......'''



#網頁每次重啟後
time = 0 
if time==0: #system loading.....
    mainurl = os.environ.get("MAIN_URL")
    DB = os.environ.get("DB")
    DB_2 = os.environ.get("DB_2")
    returnnal(mainurl,DB)#資料抓取&資料庫資料更新函式

    #資料庫載入 
    try:
        # 1. 嘗試讀取主要資料庫
        csv_dict = db_reload(DB)
        if len(csv_dict) == 0:
            returnnal(mainurl, DB)
            csv_dict = db_reload(DB)
            if len(csv_dict) == 0:
                csv_dict = db_reload(DB_2)
                raise ValueError("主資料庫內容為空，啟用備用資料庫")
    except Exception as e:
        # 2. 主要資料庫出事了（打不開或損壞），進入備用機制
        print(f" 主要資料庫異常，改讀備用檔案... 詳細原因: {e}")
        try:
            csv_dict = db_reload(DB_2)
            if len(csv_dict) == 0:
                # 💡 備用資料庫是空的，直接拋出內建錯誤並帶上你的標籤
                raise ValueError("[AllDBCorruptionError] 主要資料庫損壞，且備用資料庫內容為空或內容資料格式錯誤！")
        except FileNotFoundError:
            raise ValueError("[AllDBCorruptionError] 主要資料庫損壞，且備用資料庫不存在！")
        except Exception as backup_error:
            # 🎯 3. 當連備用資料庫也打不開或損壞時，直接拋出致命錯誤
            # 這樣日誌就會印出：RuntimeError: [AllDBCorruptionError] ...
            raise RuntimeError(
                f"[AllDBCorruptionError] 主要與備用資料庫皆已毀損或無法讀取！"
                f"原始錯誤: {backup_error}"
            )
    print(f"資料庫資料初始更新中,time:{time}")
    


app = Flask(__name__)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


'''mainpage'''

@app.route('/',methods=["GET"])
def index_get():
    global time

    time += 1 #訪問次數
    class_list = ["All","50","25","10"] #首頁列表選單

    mainurl = os.environ.get("MAIN_URL")
    DB = os.environ.get("DB")
    DB_2 = os.environ.get("DB_2")

    #定時任務
    existing_job = scheduler.get_job('daily_update_job')#檢查背景是否已經有這個排程任務
    existing_job_2 = scheduler.get_job('monthly_update_job')#檢查背景是否已經有這個排程任務
    try:
        if not existing_job:
            scheduler.add_job(            # 系統資料庫資料重載入
                id='daily_update_job',    # 建議更改 ID 以符合「天天執行」的語意
                func=db_reload,
                args=[DB],
                trigger='cron',           # 使用 cron 模式
                hour=0,                   # 12 點
                minute=30,                # 300 分
                timezone='Asia/Taipei',   # 強烈建議：鎖定台灣時間早上 10 點
                misfire_grace_time=3600,  # 錯過時間 1 小時內重新開機都會自動補做
                )
    except Exception as e:
        if not existing_job:
            scheduler.add_job(            # 系統資料庫資料重載入
                id='daily_update_job',    # 建議更改 ID 以符合「天天執行」的語意
                func=db_reload,
                args=[DB_2],
                trigger='cron',           # 使用 cron 模式
                hour=0,                   # 12 點
                minute=30,                # 300 分
                timezone='Asia/Taipei',   # 強烈建議：鎖定台灣時間早上 10 點
                misfire_grace_time=3600,  # 錯過時間 1 小時內重新開機都會自動補做
                )
            
    if not existing_job_2:            # 如果找不到任務，才重新註冊它
        scheduler.add_job(            # 資料庫更新任務
            id='monthly_update_job',  # 建議更改 ID 以符合新任務語意
            func=returnnal,
            args=[mainurl,DB],
            trigger='cron',           # 改為 cron 模式
            day=1,                    # 每個月的 1 號
            hour=23,                  # 23 點
            minute=0,                 # 00 分
            timezone='Asia/Taipei',   # 台北時間        
            misfire_grace_time=3600   # 選擇性加入：若伺服器重啟錯過時間，一小時內自動補執行
        )
    print(f"資料庫資料更新中,time:{time}")
    return render_template("index.html",class_list=class_list,time=time)



@app.route('/index.html',methods=["POST"])
def index_post():
    global time
    class_list = ["All","50","25","10"] #首頁列表選單
    # 首頁前端回傳區塊
    if request.method=="POST": 
        global return_ob   
        return_ob = request.form.get("Qusmodul-select")
        #題目問答區塊
        if return_ob == class_list[0]:
            url = os.environ.get("API_ONE")
            response_json = requests.get(url,verify=True).json()
            num = len(response_json)
        elif return_ob != class_list[0]:
            url = os.environ.get("API_TWO")
            response_json = requests.get(url,verify=True).json()
            num = len(response_json)
        else:
            return render_template("index.html",class_list=class_list,time=time)
        return render_template("testquestion.html",num=num,response_json=response_json)
    return render_template("index.html",class_list=class_list,time=time)







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
            cta = request.form.get(f"ans_{i}")   #前端隱藏的正確答案
            #cta = request.form.get(f"ans_{i}")   後端的正確答案  *// 太麻煩了不想用! 本來就是設計成刷題用的方便就好! 我超懶~ :)

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
#all_qus 可以單獨調用請求資料!
@app.route('/api/get_all',methods=["GET"])
def get_all():
    all_data = []
    for i in range(1,len([csv_dict][0])+1):
        [csv_dict][0][i]["id"] = str(i)
        all_data.append([csv_dict][0][i])
    json_api = json.dumps(all_data, ensure_ascii=True, indent=4)
    return json_api


#random_qus 試配總試題數內的任意整數(不含0)，不可以單獨調用
@app.route('/api/get_random',methods=["GET"])
def randm():
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
        if len(random_num)==int(return_ob):
            break
    json_api = json.dumps(random_qus, ensure_ascii=True, indent=4)
    return json_api


if __name__ == "__main__":
    # 設定定時排程（範例：每天台灣中午 12 點執行 = UTC 4 點）
    app.run(host='0.0.0.0',debug=True, use_reloader=False, port=8000)





