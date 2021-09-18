import requests  # install requests
import json
import time
from selenium.webdriver.support.ui import WebDriverWait  # install selenium
from seleniumwire import webdriver  # install selenium-wire


def main():
    reselt = ""
    while reselt != "Done":
        # try:
            # 初始化 WebDriver
            driver = New_Driver()
            # 初始化 Session
            s = New_Session(driver)
            # 開始選課
            Wirte_Log("Info", "開始選課")
            result = Select_Course(driver, s)
            Wirte_Log("Info", result)
            # 重置選課系統
            driver.quit()
            del driver, s
        # except Exception:
        #     Wirte_Log("Fatal", "主程式錯誤")
        #     Wirte_Log("Fatal", repr(Exception))
    input("Press ENTER to end...")


def Select_Course(driver, s):
    wantedCourseCodes = ["2241"]
    # wantedCourseCodes = input("請輸入想選的課號(以空白區分)").split(" ")

    # 取得選課網址
    url = driver.current_url[:-24]

    # 檢查課號資料是否有在 course.json 裡面
    with open("courses.json", "r") as file:
        courseJson = json.load(file)
        for courseCode in wantedCourseCodes:
            if courseCode not in list(courseJson["CourseCode"].keys()):
                Update_Course_Json(courseJson, s, courseCode, url)

    # 讀 courses.json 取得課程資訊
    courseJson = json.load(open("courses.json", "r", encoding="utf-8"))

    pos = 0
    refresh = 1
    while len(wantedCourseCodes) != 0:
        timeout = 5
        courseCode = wantedCourseCodes[pos]

        courseData = Get_Course_Data(s, courseCode, url)

        limitNumber = courseData["data"][0]["scr_precnt"]
        currentNumber = courseData["data"][0]["scr_acptcnt"]
        courseName = courseData["data"][0]["sub_name"]
        # Wirte_Log(
        #     "Info",
        #     "課程代碼:{} 課程名稱:{} 選課人數:{} 已選人數:{}".format(
        #         courseCode, courseName, currentNumber, limitNumber
        #     ),
        # )
        if currentNumber < limitNumber:
            wantedCourseData = {
                "CrsNo": courseJson["CourseCode"][courseCode]["CrsNo"],
                "PCrsNo": courseJson["CourseCode"][courseCode]["PCrsNo"],
                "SelType": courseJson["CourseCode"][courseCode]["SelType"],
            }

            # 送出選課請求
            selectCourse = s.post(
                url + "/AddSelect/AddSelectCrs", data=wantedCourseData
            )

            # 如果網站回應不成功，就重置選課系統
            if str(selectCourse.status_code) != "200":
                Wirte_Log("Error", "Http Code:{}".format(selectCourse.status_code))
                return "Error"

            #  成功加入課程
            elif "已加入" in selectCourse.text:
                Wirte_Log(
                    "Succeed", "已加入 課程代碼:{} 課程名稱:{}".format(courseCode, courseName)
                )
                timeout = 45
                # 刪除以選中的課程
                del wantedCourseCodes[pos]

            # 加選間隔太短，就多等幾秒
            elif "加選間隔太短" in selectCourse.text:
                Wirte_Log(
                    "Warning", "課程代碼:{} 課程名稱:{} 加選間隔太短".format(courseCode, courseName)
                )
                timeout = 45
            elif "已選過" in selectCourse.text:
                Wirte_Log(
                    "Warning", "課程代碼:{} 課程名稱:{} 已選過".format(courseCode, courseName)
                )
                del wantedCourseCodes[pos]
            elif "衝堂" in selectCourse.text:
                Wirte_Log(
                    "Warning", "課程代碼:{} 課程名稱:{} 衝堂".format(courseCode, courseName)
                )
                del wantedCourseCodes[pos]
            elif "限修人數已額滿" in selectCourse.text:
                Wirte_Log(
                    "Failed", "限修人數已額滿 課程代碼:{}課程名稱:{}".format(courseCode, courseName)
                )
            else:
                Wirte_Log(
                    "Failed",
                    "嘗試加選失敗 課程代碼:{}課程名稱:{} {}".format(
                        courseCode, courseName, selectCourse.text
                    ),
                )

        pos = (pos + 1) % len(wantedCourseCodes)
        # 保持網站不閒置
        refresh += 1
        if refresh % 5 == 0:
            driver.get(url + "/AddSelect/AddSelectPage")

        # 選課間隔
        for i in range(1, timeout + 1):
            time.sleep(1)

    # 全部課程選中，就結束選課系統
    return "Done"


def Wirte_Log(levelname, message):
    print("{} [{}]\t{}".format(time.strftime("%Y-%m-%d %H:%M:%S"), levelname, message))


def Get_Course_Data(s, courseCode, url):
    # 查詢課程資訊所需資料
    searchData = {
        "SearchViewModel": {
            "cmp_area": "3",
            "dgr_id": "14",
            "unt_id": "UN01",
            "cls_year": "3",
            "cls_seq": "ALL",
            "scr_selcode": courseCode,
            "scr_language": "",
            "scr_time": "",
        }
    }

    # 請求課程資料(CourseSearch.json)
    search = s.post(
        url + "/AddSelect/CourseSearch",
        data=json.dumps(searchData),
        headers={"content-type": "application/json; charset=UTF-8"},
    )
    return search.json()


def Update_Course_Json(courseJson, s, courseCode, url):
    response = Get_Course_Data(s, courseCode, url)

    # 更新 courses.json
    with open("courses.json", "w+") as file:
        # 更新json檔的資料
        updatedata = {
            "CrsNo": response["data"][0]["scr_selcode"],
            "PCrsNo": response["data"][0]["scj_sub_percode"],
            "SelType": response["data"][0]["scj_mso"],
        }
        # 更新josn檔
        courseJson["CourseCode"][courseCode] = updatedata

        # 寫入檔案
        json.dump(courseJson, file, indent=4)


def New_Session(driver):
    # 取得瀏覽器 Cookies
    cookies = driver.get_cookies()
    updateCookies = {}
    for cookie in cookies:
        updateCookies[cookie["name"]] = cookie["value"]

    # 初始化 Session
    s = requests.session()
    # 更新 Session 的 headers
    s.headers.update(dict(driver.requests[-1].headers))
    # 更新 Session 的 cookies
    s.cookies.update(updateCookies)

    return s


def New_Driver():
    # 初始化 WebDriver
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("window-size=1280,960")
    options.add_argument("headless")
    driver = webdriver.Chrome(executable_path="chromedriver.exe", options=options)
    driver.get("http://aais1.nkust.edu.tw/selcrs_dp")

    # 讀取帳號資訊
    accountJson = json.load(open("account.json", "r", encoding="utf-8"))

    # 輸入帳號
    account = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element_by_css_selector("#UserAccount")
    )
    account.send_keys(accountJson["account"])
    # 輸入密碼
    password = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element_by_css_selector("#Password")
    )
    password.send_keys(accountJson["password"])
    # 登入按鈕
    login = WebDriverWait(driver, 10).until(
        lambda driver: driver.find_element_by_css_selector("#Login")
    )
    login.click()

    # 進入選課畫面
    driver.get(driver.current_url[:-11] + "/AddSelect/AddSelectPage")
    return driver


if __name__ == "__main__":
    main()
