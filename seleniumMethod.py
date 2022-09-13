from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import json
import threading
import time


class Select_Course_Robot(threading.Thread):
    def __init__(self, account, password, Course_Code, timeout) -> None:
        threading.Thread.__init__(self)
        self.driver = self.New_Driver()
        self.account = account
        self.password = password
        self.Course_Code = Course_Code
        self.timeout = timeout

    def run(self):
        self.driver.get("https://aais6.nkust.edu.tw/selcrs_std")

        # 輸入帳號
        account = WebDriverWait(self.driver, 10).until(lambda driver: self.driver.find_element_by_css_selector("#UserAccount"))
        account.send_keys(self.account)
        # 輸入密碼
        password = WebDriverWait(self.account, 10).until(lambda driver: self.driver.find_element_by_css_selector("#Password"))
        password.send_keys(self.password)
        # 登入按鈕
        login = WebDriverWait(self.driver, 10).until(lambda driver: self.driver.find_element_by_css_selector("#Login"))
        login.click()

        # 進入選課畫面
        self.driver.get("https://aais6.nkust.edu.tw/selcrs_std/AddSelect/AddSelectPage")
        time.sleep(1)

        # 開始選課
        while True:
            status = self.Select_Course_Loop()
            time.sleep(self.timeout)
            if status == "已加入":
                print("%s  [已選上] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), self.Course_Code))
                break

        # 結束選課
        self.driver.quit()

    def Select_Course_Loop(self):
        # 查詢課號
        search = self.driver.find_element_by_css_selector("#check_selcode")
        self.driver.execute_script("arguments[0].click();", search)
        search = WebDriverWait(self.driver, 10).until(lambda driver: self.driver.find_element_by_css_selector("#scr_selcode"))
        search.send_keys(self.Course_Code)
        search = self.driver.find_element_by_css_selector("#courseSearch")
        self.driver.execute_script("arguments[0].click();", search)

        time.sleep(1)

        # 加選課程
        course_Xpath = '//*[@id="' + self.Course_Code + '"]'
        add = self.driver.find_element_by_xpath(course_Xpath)
        self.driver.execute_script("arguments[0].click();", add)

        time.sleep(3)

        # 確認是否選上
        confirm = self.driver.find_element_by_xpath(course_Xpath)

        # 選上就結束選課
        if "已加入" in confirm.text:
            return "已加入"

    # 初始化 Web Driver
    def New_Driver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("window-size=1600,1200")
        driver = webdriver.Chrome(executable_path="chromedriver.exe", options=options)
        return driver


def main():
    accountJson = json.load(open("account.json", "r", encoding="utf-8"))
    courseJson = json.load(open("course.json", "r", encoding="utf-8"))
    courses = courseJson["course"]

    robots = []
    for course in courses:
        robot = Select_Course_Robot(accountJson["account"], accountJson["password"], course, 45 * len(courses))
        robots.append(robot)
        robot.start()
        time.sleep(45)

    for robot in robots:
        robot.join()


if __name__ == "__main__":
    main()
