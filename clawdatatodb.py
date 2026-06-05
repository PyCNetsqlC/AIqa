import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import io,re,csv

def returnnal(mainurl:str,DB:str):
    #爬蟲主網頁
    url_oragin = mainurl
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url_oragin, headers=headers, timeout=10,verify=False)
    response.raise_for_status()  # 檢查請求是否成功
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    study_guidelines = soup.find_all('script')
    strfire = str(study_guidelines[-2]).lstrip("<script>elf.__next_f.push([1,").rstrip("</script>").split(",")
    study_url = [ i.lstrip('\\"url\\":\\').rstrip('\"\\') for i in strfire if ('\\"url\\":\\"' in i) and ("初級" in i) and ("試題" in i) ]
    #study_url = [ i.lstrip('\\"url\\":\\').rstrip('\"\\').replace(" ","%20") for i in strfire if ('\\"url\\":\\"' in i) and ("資訊安全" in i) and ("學習" not in i) ]

    #試題資料處理
    alldata = []
    for _ in study_url:
        dataurl = _
        data = requests.get(dataurl, headers=headers, timeout=10,verify=False)
        if data.status_code == 200:
            pdf_file = io.BytesIO(data.content)
            reader = PdfReader(pdf_file)
            total_pages = len(reader.pages)

            qus,ans,correct_answer = [],[],[]
            vv,cc = "",""

            #alldata
            for i in range(total_pages):
                sa = reader.pages[i].extract_text().split("\n")
                del(sa[0:4])
                for j in sa:
                    cc += j   

            #correct_answer
            for match in re.compile(r"([A-DＡ-Ｄ])\s+(\d+)\.").finditer(cc):
                #對應([A-D])
                answer = match.group(1)
                #對應 (\d+)
                question_num = match.group(2)
                correct_answer.append([question_num,answer])
            if len(correct_answer) != 50 :
                print(f"選項數目不對，出錯容器: correct_answer")

            # qus & ans
            cc = cc.replace("\n","")
            cc = cc.replace(" ","")
            cc = cc.replace("答案題目","")
            for i in range(len(correct_answer)):
                x = correct_answer[i][1]+correct_answer[i][0]+"."
                cc = cc.replace(x,"*")
            cc = cc.replace("(A)","\n~")
            cc = cc.replace("(B)","\n~")
            cc = cc.replace("(C)","\n~")
            cc = cc.replace("(D)","\n~")
            cc = cc.split("*")
            del(cc[0])
            for i in cc:
                x = i.split("\n")
                qus.append(x[0].replace("？","？\n").replace("。","。\n"))
                ans.append([x[1].replace("~","A. "),x[2].replace("~","B. "),x[3].replace("~","C. "),x[4].replace("~","D. ")])
            if len(qus) != len(correct_answer) :
                    print(f"問題數目不對，出錯容器: qus")
            if len(ans) != len(qus) :
                print(f"選項數目不對，出錯容器: anst")

                #alldata
            for i in range(len(qus)):
                alldata.append([qus[i].replace(" ",""),ans[i][0],ans[i][1],ans[i][2],ans[i][3],correct_answer[i][1]])
    for h in range(len(alldata)):
        alldata[h].append(f"{h+1}")
        alldata[h] = [alldata[h][len(alldata[h])-1]]+alldata[h][:len(alldata[h])-1]

    #db_csvfile
    with open(DB, mode='w+', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        # 一次寫入多行資料
        writer.writerow(["id","question","options_1","options_2","options_3","options_4","correct_answer"])
        writer.writerows(alldata)

    return alldata