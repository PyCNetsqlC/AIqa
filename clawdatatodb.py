import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import io,re,os,csv


def returnnal():
    #爬蟲主網頁
    url_oragin = "https://ipd.nat.gov.tw/ipas/certification/AIAP/learning-resources"
    #url_oragin = "https://ipd.nat.gov.tw/ipas/certification/ISE/learning-resources"

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

                
            #qus
            for j in range(len(cc)):
                if re.match(r"[1-5][0-9]\. ", cc[j:j+4]):
                    for k in range(j,len(cc)):
                        vv += cc[k]
                        if cc[k] == "？" or cc[k] == "?":
                            qus.append(vv)
                            vv = ""
                            break
                    if cc[j]=="5" and cc[j+1]=="0" and cc[j+2]==".":
                        break
                elif re.match(r" [0-9]\. ", cc[j:j+4]):
                    for k in range(j,len(cc)):
                        vv += cc[k]
                        if cc[k] == "？" or  cc[k] == "?":
                            qus.append(vv)
                            vv = ""
                            break
            for _ in range(len(qus) - 1, -1, -1):
                if "(A)" in qus[_] or "(B)" in qus[_] or "(C)" in qus[_] or "(D)" in qus[_]:
                    qus.remove(qus[_])
            for q in range(len(qus)):
                qus[q] = re.sub(r'\d+\.', '', qus[q])
            if len(qus) != len(correct_answer) :
                print(f"問題數目不對，出錯容器: qus")


            #ans
            for an in range(len(cc)):
                if cc[an] == "("  and cc[an+1] == "A":
                    for k in range(an,len(cc)):
                        vv += cc[k]
                        if cc[k] == "；" and cc[k+1] == " " and cc[k+2] == "(":
                            ans.append(vv)
                            vv = ""
                            break
                if cc[an] == "("  and cc[an+1] == "B":
                    for k in range(an,len(cc)):
                        vv += cc[k]
                        if cc[k] == "；" and cc[k+1] == " " and cc[k+2] == "(":
                            ans.append(vv)
                            vv = ""
                            break
                if cc[an] == "("  and cc[an+1] == "C":
                    for k in range(an,len(cc)):
                        vv += cc[k]
                        if cc[k] == "；" and cc[k+1] == " " and cc[k+2] == "(":
                            ans.append(vv)
                            vv = ""
                            break
                if cc[an]=="(" and cc[an+1] == "D":
                    for k in range(an,len(cc)):
                        vv += cc[k]
                        if cc[k] == " " and cc[k+1] == " ":
                            ans.append(vv)
                            vv = ""
                            break
            for _ in range(len(ans) - 1, -1, -1):
                if re.search(r"[？?]", ans[_]) and not re.search(r"[；;DＤ]", ans[_]):
                    ans.remove(ans[_])
                ans[_] = re.sub(r'\s*[A-D]\s+(?:[1-4]\d|50|[1-9])\.\s*$', '', ans[_])
            anst = [ ans[i:i+4] for i in range(len(ans)) if i%4==0]
            if len(anst) != len(qus) :
                print(f"選項數目不對，出錯容器: anst")
            
            
    #alldata
            for i in range(len(qus)):
                alldata.append([qus[i].replace(" ",""),anst[i][0],anst[i][1],anst[i][2],anst[i][3],correct_answer[i][1]])
    for h in range(len(alldata)):
        alldata[h].append(f"{h+1}")
        alldata[h] = [alldata[h][len(alldata[h])-1]]+alldata[h][:len(alldata[h])-1]


    #db_csvfile
    os.chdir(r"./db_file")
    with open('clean.csv', mode='w+', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        # 一次寫入多行資料
        writer.writerow(["id","question","options_1","options_2","options_3","options_4","correct_answer"])
        writer.writerows(alldata)
        os.chdir(r"..")

    return alldata