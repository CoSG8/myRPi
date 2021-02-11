# coding: UTF-8
# ver. 1.0.1 2021.02.11

import os
import datetime
import smbus
import time
import wiringpi as pi
from bme280 import bme280, bme280_i2c
import RPi.GPIO as GPIO
from util.mcp3204 import mcp3204

global i2c
global lcd_addr
global bme280_addr
global i2c_bus

SW_PIN = 23
BL_PIN = 4

SPI_CE = 0
SPI_SPEED = 1000000
READ_CH = 0
VREF = 3.3

interval_sec = 290

dPath = '/home/pi/myPython'
logDir = 'home_log'

# I2C Busの指定
i2c_bus = 1
# SMBusオブジェクトの取得
i2c = smbus.SMBus(i2c_bus)
# LCDのアドレス指定（i2cdetectで確認した値）
lcd_addr = 0x3e
# BME280のアドレス指定（i2cdetectで確認した値）
bme280_addr = 0x76
# mcp3204初期設定
adc = mcp3204(SPI_CE, SPI_SPEED, VREF)


# LCDの初期化（データシートを参考）
def lcd_init():
	cmds = [0x38, 0x39, 0x14, 0x79, 0x5e, 0x6a]
	i2c.write_i2c_block_data(lcd_addr, 0x00, cmds)
	time.sleep(0.2)
	lcd_clear()

# LCDの表示クリア
def lcd_clear():
	cmds = [0x0c, 0x01]
	i2c.write_i2c_block_data(lcd_addr, 0x00, cmds)
	time.sleep(0.002)
	i2c.write_byte_data(lcd_addr, 0x00, 0x06)
	time.sleep(0.2)

# LCDへ文字列を表示
# 表示する行lineと、文字列messageを指
def lcd_print_message(line, message):
	if line == 1:
		line_addr = 0x80
		i2c.write_byte_data(lcd_addr, 0x00, line_addr + 0x40)
		time.sleep(0.002)
	i2c.write_i2c_block_data(lcd_addr, 0x40, list(map(ord, message)))
	time.sleep(0.1)

# BME280初期化
def bme280_init():
	bme280_i2c.set_default_i2c_address(bme280_addr)
	bme280_i2c.set_default_bus(i2c_bus)
	bme280.setup()

# BME280から気圧と温度を取得
def bme280_data():
	data = bme280.read_all()
	return (data.temperature, data.humidity, data.pressure)

def get_illumi():
	value = adc.get_value(READ_CH)
	volt = adc.get_volt(value)
	current = volt / 10000
	u_current = current * 1000000
	illumi = 0.6 * u_current ** 0.9655
	return illumi

def get_data():
	d = datetime.datetime.now()
	date = d.strftime('%Y/%m/%d %H:%M')
	temperature, humidity, pressure = bme280_data()
	illumi = get_illumi()

	temperature = round(temperature, 1)
	humidity = round(humidity, 1)
	pressure = round(pressure, 1)
	illumi = round(illumi, 1)
	return (date, temperature, humidity, pressure, illumi)

# トグルスイッチを押したら明るさ表示
def callback(self):
	# GPIO.output(BL_PIN , GPIO.HIGH)
	start_time = time.time()
	date, temperature, humidity, pressure, illumi = get_data()
	lcd_clear()
	dispTxt = "{0}".format(round(illumi, 1))
	lcd_print_message(0, dispTxt)
	while True:
		time_count = time.time()-start_time
		if time_count  > 3:
			#GPIO.output(BL_PIN , GPIO.LOW)
			lcd_clear()
			dispTxt = "{0}".format(temperature)
			lcd_print_message(0, dispTxt)
			dispTxt = "{0}".format(humidity)
			lcd_print_message(1, dispTxt)
			break

# メイン処理
def main():
	
	# LCD初期化
	lcd_init()
	# BME280初期化
	bme280_init()  
	# GPIO初期化
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(BL_PIN, GPIO.OUT)
	GPIO.setup(SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.add_event_detect(SW_PIN, GPIO.RISING, callback=callback, bouncetime=200)

	# Data acquisition
	date, temperature, humidity, pressure, illumi = get_data()

	# Display
	print(date)
	print("{0:6.1f} C".format(temperature))
	print("{0:6.1f} %".format(humidity))
	print("{0:6.1f} hPa".format(pressure))
	print("{0:6.1f} lux".format(illumi))

	# Logging
	d = datetime.datetime.now()
	datetxt = d.strftime('%Y%m%d')
	fName ="home_log_{}.csv".format(datetxt)
	saveDir = os.path.join(*[dPath,logDir])
	os.makedirs(saveDir, exist_ok=True)
	filePath = os.path.join(*[saveDir,fName])
	f = open(filePath,'a')
	txt = date + ', ' + str(temperature) + ', ' + str(humidity) + ', ' +str(pressure) + ', ' +str(illumi) + '\n' 
	f.write(txt)
	f.close()

	# LCD
	dispTxt = "{0}".format(temperature)
	lcd_print_message(0, dispTxt)
	dispTxt = "{0}".format(humidity)
	lcd_print_message(1, dispTxt)

	# Wait
	startTime = time.time()
	while True:
		timeCount = time.time()-startTime
		if timeCount  > interval_sec:
			break

	# LCDメッセージクリア
	lcd_clear()

	# GPIO 終了処理
	GPIO.output(BL_PIN, GPIO.LOW)
	GPIO.cleanup()


if __name__== "__main__":
	main()