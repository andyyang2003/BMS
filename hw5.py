#!/usr/bin/env python3
########################################################################
# Filename    : I2CLCD1602.py
# Description : Use the LCD display data
# Author      : freenove
# modification: 2018/08/03
########################################################################
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
from Freenove_DHT import DHT
import time 
import requests
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
from gpiozero import Button, ButtonBoard, LED
import threading
from ADCDevice import *
tempup = Button(5, pull_up=True)# button 1 ( middle button) = 5
tempdown = Button(6, pull_up=True)# button 1 ( middle button) = 5
doorbutton = Button(26, pull_up=True)
celsiusbutton = Button(12, pull_up=True)
desired_temp = 69 # 65-95F
temp_readings = []

dht = DHT(17)   #create a DHT class object
alertpin = LED(18)

acpin = LED(20)
heatpin = LED(21) 
sensorpin = 23
station_id = '75' # irvine station

alert_state = True
celsius = False
door = 0
initializing = True

start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')
print(start_date)
print(end_date)
api_key = "902383d0-b9cb-41e9-a260-4a97968dafd1"
lcd_lock = threading.Lock()
motion_timer = None
lcd_timer = None
motion_active = False
log_file = "log.txt"
hvac = 0
prev_hvac = 0
humidity = 0
#i2c addresses
PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.
# Create PCF8574 GPIO adapter.
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:                             
        exit(1)
# Create LCD, passing in MCP GPIO adapter.
print('what the dog')
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)
mcp.output(3,1)     # turn on LCD backlight
lcd.begin(16,2)     # set number of LCD lines and columnsQ
def log_event(e):
    with open(log_file, "a") as file:
        file.write(f"{datetime.now().strftime('%H:%M:%S')} {e}\n")
    print(f"{datetime.now().strftime('%H:%M:%S')} {e}\n")
def get_last_valid_humidity():
    try:
        url = f"https://et.water.ca.gov/api/data?appKey={api_key}&targets={station_id}&startDate={start_date}&endDate={end_date}&dataItems=hly-rel-hum"
        response = requests.get(url)
        response.raise_for_status()
        print(response.status_code)
        if response.status_code == 200:
            log_event("API ACCESS CORRECTLY")
            data = response.json()
            for item in reversed(data['Data']['Providers'][0]['Records']):
                humidity = item['HlyRelHum']['Value']
                if humidity is not None:
                    return float(humidity)
    except (requests.RequestException, KeyError, ValueError) as e:
            print("api invalid")
    return None

def c_to_f(temp):
    return round((9/5)*temp+32)
def f_to_c(temp):
    return round((5/9)*(temp-32))
def celsius_switch():
    global celsius, desired_temp
    print("switching time")
    lcd.setCursor(5,0)
    if not celsius:
        log_event("Switched to Celsius")
        lcd.message("C")
        celsius = True
    elif celsius:
        log_event("switched back to farenheit")
        lcd.message("F")
        celsius = False
def oc_sesame():
    global door
    
    if door == 1: # open
        print("closing time")
        full_lcd_update("DOOR", "CLOSED", 6, 5)
        door = 0
        return
    if door == 0: # closed
        print("opening time")
        full_lcd_update("DOOR", "OPEN", 6, 5)
        log_event("Door Open")
        door = 1
        return
def full_lcd_update(message1, message2, x1, x2):
    
    lcd.clear()
    lcd.setCursor(x1,0)
    lcd.message(message1)
    lcd.setCursor(x2,1)
    lcd.message(message2)
    time.sleep(1)
    lcd.clear()

def motion_detected():
    global alert_state, motion_active
    if not motion_active:
        motion_active = True
        alertpin.on()
        alert_state = True

        lcd.setCursor(11, 1)
        lcd.message("L:ON ")
        #log_event("Motion Detected")
    lcd.setCursor(0, 1)
    if hvac == 0:
        lcd.message("H:OFF ")
    elif hvac == 1:
        lcd.message("H:AC  ")
    else:
        lcd.message("H:HEAT")
    threading.Timer(10, reset_motion).start()


def reset_motion():
    global alert_state, motion_active
    alertpin.off()
    alert_state = False
    motion_active = False
    lcd.setCursor(11, 1)
    lcd.message("L:OFF")
  #  log_event("Motion Reset")

def pir_motion(channel):
    if not initializing:
        motion_detected()   
def dht_sensor():
    global temp_readings, humidity

    for i in range(0,15):
            chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
            if (chk is dht.DHTLIB_OK):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
                temp_readings.append(c_to_f(dht.temperature) if not celsius else dht.temperature) #if celsius == False else dht.temperature
                print(len(temp_readings))
                print("DHT11,OK!")
                if len(temp_readings) > 3:
                    temp_readings.pop(0)
                break
            print(f"fail {i}")
            time.sleep(0.1)
    if humidity is None:
        humidity = dht.humidity
    print("Humidity : %.2f, \t Temperature : %.2f \n"%(humidity,c_to_f(dht.temperature)))
    #threading.Timer(0.1, dht_sensor).start()


def hvac_control(temp):
    global prev_hvac, hvac, desired_temp
    if celsius == True:
        temp = c_to_f(temp)
        desired_temp = c_to_f(desired_temp)
    if temp > desired_temp+3:
        hvac = 1
    elif temp < desired_temp - 3:
        hvac = 2
    else:
        hvac = 0
    if hvac != prev_hvac:
        if temp > desired_temp+3 : # AC ON
            heatpin.off()
           
            acpin.on()   
            lcd.clear()
            lcd.setCursor(7,0)
            lcd.message("AC")
            lcd.setCursor(7,1)
            lcd.message("ON")
            log_event("AC turned on")
            time.sleep(0.5)
            lcd.clear()
            lcd.setCursor(0,1)
            lcd.message("H:AC  ")
            hvac = 1    

        if temp < desired_temp-3: # HEAT ON/
            
            heatpin.on()
            acpin.off()
            lcd.clear()
            lcd.setCursor(7,0)
            lcd.message("HEAT")
            lcd.setCursor(7,1)
            lcd.message("ON")
            log_event("Heat turned on")
            
            time.sleep(0.5)
            lcd.clear()
            lcd.setCursor(0,1)
            lcd.message("H:HEAT")
            hvac = 2
        if desired_temp-3 <= temp <= desired_temp+3: # HVAC OFF
            
            heatpin.off()
            acpin.off()
            lcd.clear()
            lcd.setCursor(7,0)
            lcd.message("HVAC")
            lcd.setCursor(7,1)
            lcd.message("OFF")
            log_event("HVAC turned off")

            time.sleep(0.5)
            lcd.clear()
            lcd.setCursor(0,1)
            lcd.message("H:OFF ")
            hvac = 0
        prev_hvac = hvac
def start():
    global alert_state
    counts = 0 # Measurement counts
    global temp_readings
    index = 0
    total_loop = 0
    global initializing
    initializing = True
    global humidity
    humidity = get_last_valid_humidity()
    
    global celsius
    global door # 0 closed, 1 open

    
        
    lcd.setCursor(0,0)
    lcd.clear()
    
    while initializing == True:
        lcd.message("initializing")
        dht_sensor()
        if len(temp_readings) == 3:
                avg_temp = sum(temp_readings) / 3
                index = round(avg_temp + 0.05 * humidity)
                print(f"index {index}")
                initializing = False
    while initializing == False:
        dht_sensor()
        total_loop += 1
        print(total_loop)
        if not initializing: #fire alarm
            if index > 95:
                door = 1
                heatpin.on()
                acpin.on()
                lcd.clear()
                lcd.setCursor(5,0)
                lcd.message("FIRE")
                lcd.setCursor(6,1)
                lcd.message("RUN")

            if (door == 0): #if door closed, let hvac run
                hvac_control(index)
                lcd.setCursor(11,0)
                lcd.message("Dr:C")
            if (door == 1):
                heatpin.off()
                acpin.off()
                lcd.setCursor(0,1)
                lcd.message("H:OFF ")
                log_event("HVAC turned off")
                
                lcd.setCursor(11,0)
                lcd.message("Dr:O")
            lcd.setCursor(0,0)  # set cursor position
            lcd.message(f"{desired_temp}/{index}")# display CPU temperature]
            lcd.message(f"{'C' if celsius else 'F'}")
            lcd.setCursor(11, 1)
            lcd.message(f"L:{'ON ' if alert_state else 'OFF'}")

            

        if tempup.is_pressed and tempdown.is_pressed:
            celsius_switch()
        
def get_cpu_temp():     # get CPU temperature from file "/sys/class/thermal/thermal_zone0/temp"
    tmp = open('/sys/class/thermal/thermal_zone0/temp')
    cpu = tmp.read()
    tmp.close()
    return '{:.2f}'.format( float(cpu)/1000 ) + ' C'
def updesired(channel):
    global desired_temp
    lcd.setCursor(0,0)  # set cursor position    /
    
    if desired_temp < 95:
        old_temp = desired_temp
        desired_temp += 1
        print(f"desired temp: {desired_temp}")
        log_event(f"temp turned up from {old_temp} to {desired_temp}")

        lcd.message(f"{desired_temp}")
def downdesired(channel):
    global desired_temp
    lcd.setCursor(0,0)  # set cursor position
    
    if desired_temp > 65:
        old_temp = desired_temp

        desired_temp -= 1
        print(f"desired temp: {desired_temp}")
        log_event(f"temp turned down from {old_temp} to {desired_temp}")
        lcd.message(f"{desired_temp}")
def get_time_now():     # get system time
    return datetime.now().strftime('%H:%M')
def myclock():
    while True:
        current = get_time_now()
        if lcd_lock.acquire(blocking=False):
            if not initializing:
                try:
                    time.sleep(0.5)
                    lcd.setCursor(5,1)
                    lcd.message(current)
                finally:
                    lcd_lock.release()
            if initializing:
                try:
                    lcd.setCursor(0,1)
                    lcd.message(current)
                finally:
                    lcd_lock.release()
                    
        time.sleep(1)
def destroy():
    
    lcd.clear()
    
def setup():
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(sensorpin, GPIO.IN)    
    GPIO.add_event_detect(sensorpin, GPIO.RISING, callback=pir_motion)
    

    tempup.when_pressed = updesired
    tempdown.when_pressed = downdesired   
    doorbutton.when_released = oc_sesame
    celsiusbutton.when_pressed = celsius_switch


if __name__ == '__main__':
    print ('Program is starting ... ')
    setup()
    #threading.Thread(target=dht_sensor, daemon=True).start()
    try:
        threading.Thread(target=start, daemon=True).start()
        input("press enter\n")
    except KeyboardInterrupt:
        destroy()
    finally:
        GPIO.cleanup()