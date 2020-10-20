# coding: UTF-8 
# ver. 1.2 2020.10.19

import cv2
from pathlib import Path
import RPi.GPIO as GPIO
import datetime
import picamera
import wiringpi as pi
import time
import os
import datetime
import smbus
import glob
import re
import numpy as np
from bme280 import bme280, bme280_i2c

global interval_sec
global runTime_min
global i2c
global lcd_addr
global bme280_addr
global i2c_bus
global dPath

cam = picamera.PiCamera()
SENSOR_PIN = 18
LED_PIN = 4

interval_sec = 60
runTime_min = 120

# I2C Busの指定
i2c_bus = 1
# SMBusオブジェクトの取得
i2c = smbus.SMBus(i2c_bus)
# LCDのアドレス指定（i2cdetectで確認した値）
lcd_addr = 0x3e
# BME280のアドレス指定（i2cdetectで確認した値）
bme280_addr = 0x76

dPath = '/home/pi/myPython'
imgDir = 'piPhoto_3'
logDir = 'humidity_Log_3'

# openCV
HAAR_FILE = "/home/pi/opencv/data/haarcascades/haarcascade_frontalface_default.xml"
cascade = cv2.CascadeClassifier(HAAR_FILE)

# BME280初期化
def bme280_init():
  bme280_i2c.set_default_i2c_address(bme280_addr)
  bme280_i2c.set_default_bus(i2c_bus)
  bme280.setup()

# BME280から気圧と温度を取得
def bme280_data():
  data = bme280.read_all()
  return (data.temperature, data.humidity, data.pressure,)

def LED_on():
 GPIO.output(LED_PIN, GPIO.HIGH)
 start_time = time.time()
 while True:
  time_count = time.time()-start_time
  if time_count > 4:
   GPIO.output(LED_PIN, GPIO.LOW)
   break

def take_photo():
 d = datetime.datetime.now()
 datetxt = d.strftime('%Y%m%d_%H_%M')
 fName ="piPhoto_{}.jpg".format(datetxt)
 saveDir = os.path.join(*[dPath,imgDir])
 os.makedirs(saveDir, exist_ok=True)
 # iDir = os.path.abspath(os.path.dirname('__file__'))
 # filePath = os.path.join(*[iDir,'piPhoto',fName])
 filePath = os.path.join(*[saveDir,fName])
 print('save ' + filePath)
 LED_on()
 cam.capture(filePath) 

def check_humidity():
 d = datetime.datetime.now()
 dateData = d.strftime('%Y/%m/%d %H:%M')
 temperature, humidity, pressure = bme280_data()
 #display
 print(dateData)
 print("{0:7.2f} C".format(temperature))
 print("{0:7.2f} %".format(humidity))
 print("{0:7.2f} hPa".format(pressure))
 #save
 datetxt = d.strftime('%Y%m%d')
 fName ="humidity_log_{}.csv".format(datetxt)
 saveDir = os.path.join(*[dPath,logDir])
 os.makedirs(saveDir, exist_ok=True)
 filePath = os.path.join(*[saveDir,fName])
 f = open(filePath,'a')
 txt = dateData + ', ' + str(round(temperature, 2)) + ', ' + str(round(humidity,2)) + ', ' +str(round(pressure,2)) + '\n' 
 f.write(txt)
 f.close()

def gammaConv(gammaVal,img):
# img = 255 * (img / 255) ** (1 / gammaVal)
# img_gamma = np.clip(img, 0, 255).astype(np.uint8)
 gamma_cvt = np.zeros((256,1), dtype=np.uint8)
 for i in range(256):
  gamma_cvt[i][0] = 255*(float(i)/255) ** (1.0 / gammaVal)
 img_gamma = cv2.LUT(img, gamma_cvt)
 return img_gamma

# openCV
def check_face():
 img_clothes = []
 gamma = 1.5
 imgPath = os.path.join(*[dPath,imgDir])
 images = glob.glob(os.path.join(imgPath,'*.jpg'))
 images.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

 for fname in images:
  filename = Path(fname).stem
  print(filename)
  img = cv2.imread(fname)
  img_gamma = gammaConv(gamma,img)
  img_g = cv2.imread(fname,0)
  face = cascade.detectMultiScale(img_g,minSize=(200,200))

  if len(face) == 1:
   H, W, ch = img.shape
   for x,y,w,h in face:
    img_cropped = img_gamma[y+int(h*1.1):y+int(h*2.6),x-int(h*0.4):x+int(h*1.1) :]
    img_face = img_gamma.copy()
   #cv2.rectangle(img_face, (x,y),(x+w,y+h),(0,0,255),1)

    filename_face = filename + '_face.jpg'
    saveDir = os.path.join(*[Path(fname).parent,'face'])
    os.makedirs(saveDir, exist_ok=True)
    savePath = os.path.join(*[saveDir ,filename_face])
    cv2.imwrite(savePath,img_face)

    img_resized = cv2.resize(img_cropped, dsize=(300,300))
    img_clothes.append(img_resized)

    filename_cloth = filename + '_cloth.jpg'
    saveDir = os.path.join(*[Path(fname).parent,'cloth'])
    os.makedirs(saveDir, exist_ok=True)
    savePath = os.path.join(*[saveDir ,filename_cloth])
    cv2.imwrite(savePath,img_resized)


def main():
 # Initialization
 cam.resolution = (900,1200)
 cam.rotation  = 180
 bme280_init()  
 GPIO.setmode(GPIO.BCM)
 pi.wiringPiSetupGpio()
 pi.pinMode( SENSOR_PIN, pi.INPUT )
 GPIO.setup(LED_PIN, GPIO.OUT)
 photoTime = 0
 bPhotoReady = True

 # Check humidity at once
 check_humidity()

 # Loop
 startTime = time.time()
 while True:
  timeCount = time.time()-startTime
  if bPhotoReady:
   if pi.digitalRead(SENSOR_PIN) == pi.HIGH:
    take_photo()
    photoTime = timeCount
    bPhotoReady = False
  
  if timeCount > photoTime + interval_sec:
   bPhotoReady = True

  if timeCount  > runTime_min*60:
   check_humidity()
   break
 
 check_face()

 GPIO.output(LED_PIN, GPIO.LOW) 
 GPIO.cleanup()

if __name__== "__main__":
 main()
