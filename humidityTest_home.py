# coding: UTF-8
# ver. 2.1 2020.05.08

import os
import datetime
import smbus
import time
from bme280 import bme280, bme280_i2c
import RPi.GPIO as GPIO

global i2c
global lcd_addr
global bme280_addr
global i2c_bus

SW_PIN = 23
BL_PIN = 4

# I2C Busの指定
i2c_bus = 1
# SMBusオブジェクトの取得
i2c = smbus.SMBus(i2c_bus)
# LCDのアドレス指定（i2cdetectで確認した値）
lcd_addr = 0x3e
# BME280のアドレス指定（i2cdetectで確認した値）
bme280_addr = 0x76

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
	return (data.temperature, data.humidity, data.pressure,)

# トグルスイッチを押したら1秒バックライト点灯
def callback(self):
	GPIO.output(BL_PIN , GPIO.HIGH)
	start_time = time.time()
	while True:
		time_count = time.time()-start_time
		if time_count  > 1:
			GPIO.output(BL_PIN , GPIO.LOW)
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
	GPIO.add_event_detect(SW_PIN, GPIO.RISING, callback=callback, bouncetime=100)

	temperature, humidity, pressure = bme280_data()
	d = datetime.datetime.now()
	dateData = d.strftime('%Y/%m/%d %H:%M')

	# display
	print(dateData)
	print("{0:7.2f} C".format(temperature))
	print("{0:7.2f} %".format(humidity))
	print("{0:7.2f} hPa".format(pressure))

	# LCD
	dispTxt = "{0}".format(round(temperature, 1))
	lcd_print_message(0, dispTxt)
	dispTxt = "{0}".format(round(humidity, 1))
	lcd_print_message(1, dispTxt)

	# Logging
	dPath = '/home/pi/myPython/humidityTest_v2_log'
	datetxt2 = d.strftime('%Y%m%d')
	fName = 'humidityLog_v2_'  + datetxt2 + '.csv'
	filePath = os.path.join(*[dPath,fName])
	f = open(filePath,'a')
	txt = dateData + ', ' + str(temperature) + ', ' + str(humidity) + ', ' +str(pressure) + '\n' 
	f.write(txt)
	f.close()

	# wait
	startTime = time.time()
	while True:
		timeCount = time.time()-startTime
		if timeCount  > 290:
			break

	# LCDメッセージクリア
	lcd_clear()
	# GPIO 終了処理
	GPIO.output(BL_PIN, GPIO.LOW)
	GPIO.cleanup()


if __name__== "__main__":
	main()