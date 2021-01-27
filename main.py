from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from login import *
import time


# assert "Robinhood" in browser.title

def update_chromedriver():
    # automate updating chromedriver
    return 0

def login(browser):
    temp = browser.find_element_by_id("Email")
    temp.send_keys(bb_user)
    temp = browser.find_element_by_id("Password")
    temp.send_keys(bb_pass)
    temp.send_keys(Keys.RETURN)

def exit():
    driver.quit()

def main():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    browser = webdriver.Chrome(executable_path="C:\\Users\\mutia\\Desktop\\qf\\chromedriver.exe", chrome_options=chrome_options)
    browser.get("https://members.blackboxstocks.com/blackbox")
    login(browser)

    # clicks on alert stream
    time.sleep(10)
    browser.find_element_by_id("sort-alert-stream").click()

    # clicks on filter
    time.sleep(1)
    browser.find_element_by_id("spanAlertStreamFilters").click()
    time.sleep(1)
    browser.find_element_by_id("chkAlertStreamBlock").click()
    browser.find_element_by_id("chkAlertStream52WeekLow").click()
    browser.find_element_by_id("chkAlertStreamAll").click()
    browser.find_element_by_xpath('//*[@id="alertStreamFilters"]/div/div/div[3]/button[1]').click()
    browser.find_element_by_id("menuItemOptions").click()
    
    # for row in rows:
    #     time.sleep(.05)
    #     cols = row.find_elements(By.TAG_NAME, "td")
    #     temp = ""
    #     for col in cols:
    #         temp += col.text + "; "
    #     print(temp)


    # filter 
    filter = "BABA"
    temp = browser.find_element_by_id("loadSymbolOptionsFromMi")
    temp.send_keys(filter)
    temp.send_keys(Keys.RETURN)

    #unfilter
    time.sleep(10)
    browser.find_element_by_id("loadSymbolOptionsFromMi").clear()
    browser.find_element_by_xpath('//*[@id="alertStreamFiltered"]/span[1]/a').click()
    browser.find_element_by_xpath('//*[@id="optionsFiltered"]/span[1]/a').click()

    # print alert stream
    time.sleep(5)
    # sbar = browser.find_element_by_xpath('//*[@id="alertStreamBody"]/div[2]/div')
    scroll = ActionChains(browser)
    # print(browser.find_element_by_id("alertStreamBody").text)
    # scroll.move_to_element(temp).send_keys(Keys.PAGE_DOWN).perform()
    # time.sleep(1)
    for i in range(1,40,9):
        # print(browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i}]').text)
        # print(browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i+1}]').text)
        # temp = browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i}]')
        # scroll.move_to_element(temp).send_keys(Keys.PAGE_DOWN).perform()
        # time.sleep(1)
        print("start 10")
        for j in range(10):
            print(browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i+j}]').text)
        print("done 10")
        temp = browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i+10}]')
        for j in range(4):
            scroll.move_to_element(temp).send_keys(Keys.PAGE_DOWN).perform()
        time.sleep(2)

    return 0

main()