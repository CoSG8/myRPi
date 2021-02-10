# coding: UTF-8
# ver. 1.0 2021.02.10

import os
import datetime
import smbus
import time
import wiringpi as pi
from bme280 import bme280, bme280_i2c
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
logDir = 'home_log_backup'

# I2C Busの指定
i2c_bus = 1
# SMBusオブジェクトの取得
i2c = smbus.SMBus(i2c_bus)
# BME280のアドレス指定（i2cdetectで確認した値）
bme280_addr = 0x76
# mcp3204初期設定
adc = mcp3204(SPI_CE, SPI_SPEED, VREF)


# BME280初期化
def bme280_init():
	bme280_i2c.set_default_i2c_address(bme280_addr)
	bme280_i2c.set_default_bus(i2c_bus)
	bme280.setup()

# BME280から気圧と温度を取得
def bme280_data():
	data = bme280.read_all()
	return (data.temperature, data.humidity, data.pressure,)

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

# メイン処理
def main():
	
	# BME280初期化
	bme280_init()  

	# Data acquisition
	date, temperature, humidity, pressure, illumi = get_data()

	# Display
	print(dateData)
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

	# Wait
	startTime = time.time()
	while True:
		timeCount = time.time()-startTime
		if timeCount  > interval_sec:
			break


if __name__== "__main__":
	main()