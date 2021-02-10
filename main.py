from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from login import *
import time
import requests
import urllib
from threading import Timer

time_to_sell = 1800.0 #default 1800.0


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
    # TODO: add time constraints (stop buying after 3:30 cause can't sell)
    # https://stackoverflow.com/questions/30896110/in-python-check-if-current-time-is-less-than-specific-time/30896304


    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    browser = webdriver.Chrome(executable_path=path, chrome_options=chrome_options)
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

    cur = ""
    updated = 0 # if looking at new ticker
    while True:
        # search for next stock to buy
        try:
            next = browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{1}]').text
        except Exception as e:
            print("search error")
            try:
                browser.find_element_by_id("loadSymbolOptionsFromMi").clear()
                browser.find_element_by_xpath('//*[@id="alertStreamFiltered"]/span[1]/a').click()
                browser.find_element_by_xpath('//*[@id="optionsFiltered"]/span[1]/a').click()
                updated = 0
            except Exception as e:
                    print("reset error at search")
            continue

        if cur != next:
            cur = next
            updated = 1
            ticker = cur.split()[1]
            print(f"getting data for {ticker}")

            # filter
            filter = ticker
            temp = browser.find_element_by_id("loadSymbolOptionsFromMi")
            temp.send_keys(filter)
            temp.send_keys(Keys.RETURN)

            time.sleep(1)
            optionsBody = browser.find_element_by_id('optionsBody').text
            optionsBody = optionsBody.split("\n")

            call_vol = 0
            put_vol = 0
            for trade in optionsBody:
                data = trade.split()
                try:
                    # print(data[1], data[4], data[8], data)
                    if data[4] == 'CALL':
                        if data[8][-1] == 'K':
                            call_vol += float(data[8][1:-1])*1000
                        if data[8][-1] == 'M':
                            call_vol += float(data[8][1:-1]) * 1000000
                    else:
                        if data[8][-1] == 'K':
                            put_vol += float(data[8][1:-1])*1000
                        if data[8][-1] == 'M':
                            call_vol += float(data[8][1:-1])*1000000
                except Exception as e:
                    print(f'get data error for {ticker}')
                    break

            if call_vol+put_vol == 0:
                print(f"NO VOLUME for {ticker}")
                continue
            elif call_vol/(call_vol+put_vol) > .7:
                # buy, temporary write to file
                file = open("log.txt", "a")
                file.write(f"Buy {ticker} @ {query(ticker)}\n")
                file.close()
                print(f"Buy {ticker} @ {query(ticker)}\n")

                # sell in 30 mins, temporary write to file
                t = Timer(time_to_sell, timer_query, args=[ticker])
                t.start()
            else:
                print(f"call_vol {call_vol}, put_vol {put_vol}, percent {call_vol/(call_vol+put_vol)}")

        if updated:
            try:
                browser.find_element_by_id("loadSymbolOptionsFromMi").clear()
                browser.find_element_by_xpath('//*[@id="alertStreamFiltered"]/span[1]/a').click()
                browser.find_element_by_xpath('//*[@id="optionsFiltered"]/span[1]/a').click()
                updated = 0
            except Exception as e:
                    print("reset error at reset")
        time.sleep(1)

    # browser.find_element_by_id("optionsFilter").click()
    # time.sleep(1)
    # browser.find_element_by_id("chkOptionsFlowEtf").click()
    # browser.find_element_by_xpath('//*[@id="optionsFlowFilters"]/div/div/div[3]/button[1]').click()


    return 0

def query(symbol):
    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/quotes"
    payload={'apikey':td_api_key}
    # headers = {'Authorization': }
    content = requests.get(url=endpoint, params=payload).json() #headers=headers
    return content[symbol]['lastPrice']

def timer_query(symbol):
    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/quotes"
    payload={'apikey':td_api_key}
    # headers = {'Authorization': }
    content = requests.get(url=endpoint, params=payload).json() #headers=headers
    last_price = content[symbol]['lastPrice']

    file = open("log.txt", "a")
    file.write(f"Sell {symbol} @ {query(symbol)}\n")
    file.close()


def api_call_eg():
    symbol = "GME"
    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/pricehistory"
    payload = {'apikey': td_api_key,
               'periodType':'day',
               'period':1,
               'frequencyType':'minute',
               'frequency':'30'
               }

    content = requests.get(url=endpoint, params=payload)
    data = content.json()
    for key in data:
        print(key, data[key])

def auth():
    # init browser
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    browser = webdriver.Chrome(executable_path="C:\\Users\\mutia\\Desktop\\qf\\chromedriver.exe", chrome_options=chrome_options)

    # components of url
    method = 'GET'
    url = 'https://auth.tdameritrade.com/auth?'
    client_code = td_api_key+'@AMER.OAUTHAP'
    payload = {'response_type':'code', 'redirect_uri':'http://localhost', 'client_id':client_code}

    # build url
    built_url = requests.Request(method, url, params=payload).prepare()
    built_url = built_url.url
    browser.get(built_url)

    # enter username, password
    temp = browser.find_element_by_id("username0")
    temp.send_keys(td_api_user)
    temp = browser.find_element_by_id("password1")
    temp.send_keys(td_api_pass)
    temp.send_keys(Keys.RETURN)
    browser.find_element_by_id('accept').click()


main()
# api_call_eg()
# auth()


#print stuff test
# # for row in rows:
# #     time.sleep(.05)
# #     cols = row.find_elements(By.TAG_NAME, "td")
# #     temp = ""
# #     for col in cols:
# #         temp += col.text + "; "
# #     print(temp)
#
#
# # filter
# # filter = "BABA"
# # temp = browser.find_element_by_id("loadSymbolOptionsFromMi")
# # temp.send_keys(filter)
# # temp.send_keys(Keys.RETURN)
#
# # unfilter
# # time.sleep(10)
# # browser.find_element_by_id("loadSymbolOptionsFromMi").clear()
# # browser.find_element_by_xpath('//*[@id="alertStreamFiltered"]/span[1]/a').click()
# # browser.find_element_by_xpath('//*[@id="optionsFiltered"]/span[1]/a').click()
#
# # print alert stream
# time.sleep(5)
# # sbar = browser.find_element_by_xpath('//*[@id="alertStreamBody"]/div[2]/div')
# scroll = ActionChains(browser)
# # print(browser.find_element_by_id("alertStreamBody").text)
# # scroll.move_to_element(temp).send_keys(Keys.PAGE_DOWN).perform()
# # time.sleep(1)
# for i in range(1, 40, 9):
#     # print(browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i}]').text)
#     # print(browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i+1}]').text)
#     # temp = browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i}]')
#     # scroll.move_to_element(temp).send_keys(Keys.PAGE_DOWN).perform()
#     # time.sleep(1)
#     print("start 10")
#     for j in range(10):
#         print(browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i+j}]').text)
#     print("done 10")
#     temp = browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{i+10}]')
#     for j in range(4):
#         scroll.move_to_element(temp).send_keys(Keys.PAGE_DOWN).perform()
#     time.sleep(2)
