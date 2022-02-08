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
from datetime import datetime

import os
import math

import email
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

time_to_sell = 900.0 #default 1800.0
# log_path = "log.txt"
log_path = "test.txt"
access_token = ""
## TD set up below
perTransaction = 200
slipAdjust = 0.02
minPrice = 8
stopPercent = 0.998
shares = 0
volPercent = 0.05

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
    # browser.find_element_by_id("chkAlertStream52WeekLow").click()
    browser.find_element_by_id("chkAlertStreamAll").click()
    # Set filter button
    # browser.find_element_by_xpath('//*[@id="alertStreamFilters"]/div/div/div[3]/button[1]').click()
    browser.find_element_by_xpath('/html/body/div[7]/div[3]/button[1]').click()
    browser.find_element_by_id("menuItemOptions").click()

    cur_ticker = ""
    updated = 0 # if looking at new ticker
    email_results = False
    while True:
        # check if markets open
        cur_time = datetime.now().time()
        cur_h = cur_time.hour
        cur_m = cur_time.minute/60

        if cur_h+cur_m <= 9.5 or cur_h+cur_m >= 16:
            # print(f"{cur_time}, market not open")

            # email results at end of day (4 EST)
            if not email_results:
                email_results = True
                print("emailing results")
                email(log_path)
                print("clearing log")
                os.remove(log_path)
                print("sleeping")
                # time.sleep(60 * 60 * 17) # sleep overnight
                # email to james
            time.sleep(5) # sleep for 30 sec while waiting for market open
            continue

        # don't let it try to buy stocks
        if cur_h+cur_m >= 15.3:
            continue

        email_results = False # if market open again, need to email results

        # search for next stock to buy
        try:
            next = browser.find_element_by_xpath(f'//*[@id="alertStreamBody"]/tr[{1}]').text
            next_ticker = next.split()[1]
        except Exception as e:
            # print("search error")
            try:
                browser.find_element_by_id("loadSymbolOptionsFromMi").clear()
                browser.find_element_by_xpath('//*[@id="alertStreamFiltered"]/span[1]/a').click()
                browser.find_element_by_xpath('//*[@id="optionsFiltered"]/span[1]/a').click()
                updated = 0
            except Exception as e:
                # print("reset error at search")
            continue

        if next_ticker != cur_ticker:
            cur_ticker = next_ticker
            updated = 1
            # print(f"getting data for {cur_ticker}")

            # filter
            filter = cur_ticker
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
                    # print(f'get data error for {cur_ticker}')
                    break

            if call_vol+put_vol == 0:
                # print(f"NO VOLUME for {cur_ticker}")
                continue
            elif call_vol/(call_vol+put_vol) > .7:
                # buy, temporary write to file
                price, vol = query(cur_ticker)

                #shares calculation
                if price > perTransaction:
                    shares=1
                elif perTransaction/price < volPercent*vol:
                    shares = int(perTransaction/price)
                else:
                    shares = int(volPercent*vol)

                # cancel buy if not executed after a minute, if not cancelled (already executed), cancel stop loss after 30 and place sell order
                try:
                    # print("buy", shares)
                    # order_id = buy(cur_ticker, price, shares)
                    # print("create sell time")
                    # t_sell = Timer(60, cancel_buy, args=[order_id, cur_ticker, shares])
                    # print("start sell")
                    t_sell.start()
                except Exception as e:
                    print("TD BUY ERROR")
                    print(e)

                # log entry for buy
                file = open(log_path, "a")
                file.write(f"Buy;{cur_ticker};{price}\n")
                file.close()
                # print(f"Buy;{cur_ticker};{price}\n")

                # sell in 30 mins, temporary write to file
                t = Timer(time_to_sell, timer_query, args=[cur_ticker])
                t.start()

            else:
                pass
                # print(f"call_vol {call_vol}, put_vol {put_vol}, percent {call_vol/(call_vol+put_vol)}")

        if updated:
            try:
                browser.find_element_by_id("loadSymbolOptionsFromMi").clear()
                browser.find_element_by_xpath('//*[@id="alertStreamFiltered"]/span[1]/a').click()
                browser.find_element_by_xpath('//*[@id="optionsFiltered"]/span[1]/a').click()
                updated = 0
            except Exception as e:
                # print(e)
                # print("reset error at reset")
        time.sleep(1)

    # browser.find_element_by_id("optionsFilter").click()
    # time.sleep(1)
    # browser.find_element_by_id("chkOptionsFlowEtf").click()
    # browser.find_element_by_xpath('//*[@id="optionsFlowFilters"]/div/div/div[3]/button[1]').click()


    return 0

# can replace query code
# replace endpoint with https://api.tdameritrade.com/v1/accounts/{accountId}/orders and your account id
# important info https://github.com/areed1192/td-ameritrade-python-api/blob/master/td/client.py
#   _make_request and place_order

def buy(symbol, price, shares):
    access_token = get_new_access_token()
    request_session = requests.Session()
    request_session.verify = True
    print(shares, access_token)
    slipAdjust = 0.02
    minPrice = 10
    volPercent = 0.10
    request_request = requests.Request(
        method='post',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        url='https://api.tdameritrade.com/v1/accounts/279053763/orders',  # replace {accountID} with accountId
        params=None,
        data=None,
        json={
          "orderType": "MARKET",
          "session": "NORMAL",
          "duration": "DAY",
          "orderStrategyType": "SINGLE",
          "orderLegCollection": [
            {
              "instruction": "Buy",
              "quantity": shares,
              "instrument": {
                "symbol": symbol,
                "assetType": "EQUITY"
              }
            }
          ]
        }

  # here you put the json for the order
    ).prepare()

    response: requests.Response = request_session.send(request=request_request)

    request_session.close()

    print(response.status_code)
    response_headers = response.headers
    print(response_headers)
    order_id = response_headers['Location'].split('orders/')[1]
    return order_id

def stop(symbol, price, shares):
    access_token = get_new_access_token()
    request_session = requests.Session()
    request_session.verify = True
    print(shares, access_token)
    slipAdjust = 0.02
    minPrice = 8
    stopPercent = 0.998
    volPercent = 0.10
    request_request = requests.Request(
        method='post',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        url='https://api.tdameritrade.com/v1/accounts/279053763/orders',  # replace {accountID} with accountId
        params=None,
        data=None,
        json={
            "orderType": "TRAILING_STOP",
            "session": "NORMAL",
            "stopPriceLinkBasis": "BID",
            "stopPriceLinkType": "VALUE",
            "stopPriceOffset": round(price-price*stopPercent, 2),
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "SELL",
                    "quantity": shares,
                    "instrument": {
                        "symbol": symbol,
                        "assetType": "EQUITY"
                    }
                }
            ]
        }

  # here you put the json for the order
    ).prepare()

    response: requests.Response = request_session.send(request=request_request)

    request_session.close()

    print(response.status_code)
    response_headers = response.headers
    print(response_headers)
    order_id = response_headers['Location'].split('orders/')[1]
    return order_id

def log_query(symbol):
    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/quotes"
    payload={'apikey':td_api_key}
    # headers = {'Authorization': }
    content = requests.get(url=endpoint, params=payload).json() #headers=headers
    return content[symbol]['lastPrice']

def query(symbol):
    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/quotes"
    payload={'apikey':td_api_key}
    # headers = {'Authorization': }
    content = requests.get(url=endpoint, params=payload).json() #headers=headers
    return content[symbol]['lastPrice'], content[symbol]['totalVolume']

def timer_query(symbol):
    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/quotes"
    payload={'apikey':td_api_key}
    # headers = {'Authorization': }
    content = requests.get(url=endpoint, params=payload).json() #headers=headers
    last_price = content[symbol]['lastPrice']

    file = open(log_path, "a")
    file.write(f"Sell;{symbol};{query(symbol)}\n")
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

def email(file):
    sender_email = "qfthesis2022@gmail.com"
    dest_email = "jamesqu3@gmail.com"
    password = email_pass

    # create multipart email
    message = MIMEMultipart()
    message["Subject"] = "Daily Log"
    message["From"] = sender_email
    message["To"] = dest_email

    filename = file

    # Open file in binary mode
    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, dest_email, text)


def get_new_access_token() -> str:
    method = 'post'
    url = 'https://api.tdameritrade.com/v1/oauth2/token'
    client_code = td_api_key+'@AMER.OAUTHAP'

    body = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_code}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    session = requests.Session()

    request = requests.Request(method=method, headers=headers, url=url, data=body).prepare()
    response: request.Response = session.send(request=request)
    return response.json()['access_token']

def cancel(order_id):
    access_token = get_new_access_token()
    request_session = requests.Session()
    request_session.verify = True

    request_request = requests.Request(
        method='delete',
        headers={
            'Authorization': f'Bearer {access_token}'
        },
        url=f'https://api.tdameritrade.com/v1/accounts/279053763/orders/{order_id}'
    ).prepare()

    response: requests.Response = request_session.send(request=request_request)

    request_session.close()

    print(response.status_code)
    print(response.headers)

    return response.status_code

def timer_sell(ticker, shares):
    price, vol = query(ticker)

    slipAdjust = 0.02
    minPrice = 8
    stopPercent = 0.998
    volPercent = 0.05

    access_token = get_new_access_token()
    request_session = requests.Session()
    request_session.verify = True

    request_request = requests.Request(
        method='post',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        url='https://api.tdameritrade.com/v1/accounts/279053763/orders',  # replace {accountID} with accountId
        params=None,
        data=None,
        json={
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": round(price-slipAdjust, 2),
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "SELL",
                    "quantity": shares,
                    "instrument": {
                    "symbol": ticker,
                    "assetType": "EQUITY"
                    }
                }
            ]
        }

        # here you put the json for the order
    ).prepare()

    response: requests.Response = request_session.send(request=request_request)

    request_session.close()

    print(response.status_code)
    response_headers = response.headers
    print(response_headers)
    order_id = response_headers['Location'].split('orders/')[1]
    return order_id

def cancel_buy(order_id, ticker, shares):
    # thirty_min_later = datetime.now() + timedelta(minutes=30)
    # thirty_min_later = f"{thirty_min_later.year}-{thirty_min_later.month}-{thirty_min_later.day}T{thirty_min_later.hour}:{thirty_min_later.minute}:{thirty_min_later.second}"

    if cancel(order_id) == 400:
        price, vol = query(ticker)
        stop_id=stop(ticker,price, shares)
        t_cancel_stop_loss = Timer(770, cancel, args=[stop_id])
        t_cancel_stop_loss.start()
        t_place_sell = Timer(900, timer_sell, args=[ticker, shares])
        t_place_sell.start()

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
