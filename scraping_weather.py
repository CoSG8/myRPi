#!/usr/bin/env python3
#encoding=utf-8
## scraping_weather pi
## スクリプト名：scraping_weather.py
## 機能概要　　：Google天気予報から天気を取得
## Presented by RaspiMAG 2020/10
## Programmed by pochi_ken
## Modified by Akito Kosugi
## v. 1.0.4 06.28.2021

# ライブラリー定義
import RPi.GPIO as GPIO
import smbus
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def scraping():
    options = Options()
    options.binary_location = '/usr/bin/chromium-browser'
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')
    driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', options=options)
    target_url = 'https://tenki.jp/forecast/3/16/4410/13211'
    driver.get(target_url)
    html = driver.page_source.encode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    weather_res = soup.find(class_ = 'today-weather')
    weather_telop = weather_res.find(class_ = "weather-telop").text
    high_temp = weather_res.find(class_ = "high-temp temp").text
    rain_probability_all = weather_res.find(class_ = "rain-probability").text
    rain_probability_temp = rain_probability_all.splitlines()
    rain_probability_pm = rain_probability_temp[4]

    driver.quit()
    return weather_telop, high_temp, rain_probability_pm

#LCD AQM0802 data process function
def lcd_ctrl(data):
    i2c.write_byte_data(_addr, 0x00, data)
    time.sleep(0.1)
def lcd_display(msg):
    mlist=[]
    for letter in msg:
        mlist.append(ord(letter))
    i2c.write_i2c_block_data(_addr, 0x40, mlist)
    time.sleep(0.1)
def lcd_init():
    for dat in LCD_init:
        lcd_ctrl(dat)

def forecast(todays_weather):
    # 点灯LEDの選択
    if todays_weather == "曇":
        sel = "Cloudy"
    elif todays_weather == "晴":
        sel = "Sunny"
    elif todays_weather == "雨":
        sel = "Rainy"
    elif todays_weather == "雪":
        sel = "Snowy"
    elif todays_weather == "晴のち曇":
        sel = "Sun/Clo"
    elif todays_weather == "晴のち雨":
        sel = "Sun/Rai"
    elif todays_weather  == "雨のち曇":
        sel = "Rai/Clo"
    elif todays_weather  == "雨のち晴":
        sel = "Rai/Sun"
    elif todays_weather  == "曇一時雨":
        sel = "Clo-Rai"
    elif todays_weather == "晴一時雨":
        sel = "Sun-Rai"
    else:
        sel = "Forecast"
    return sel

# Main
# setting up GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
i2c = smbus.SMBus(1)
_addr=0x3e
LCD_init= [0x38, 0x39, 0x14, 0x73, 0x56, 0x6c, 0x38, 0x01, 0x0f, 0x01]
LCD_l2nd=0x40+0x80
#lcd_init()
#lcd_display("Weather")

try:
    while True:
        todays_weather, todays_high_temp, todays_rain_prob = scraping()
        print("現在の天気:" + todays_weather)
        print("最高気温:" + todays_high_temp)
        print("降水確率:" + todays_rain_prob)
        sel = forecast(todays_weather)
        lcd_init()
        lcd_display(sel)
        time.sleep(1)

        lcd_ctrl(LCD_l2nd)
        lcd_display(todays_high_temp+todays_rain_prob)
        time.sleep(1)

except KeyboardInterrupt:
    pass

GPIO.cleanup()
