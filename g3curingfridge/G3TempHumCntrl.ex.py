#!/usr/bin/python

import subprocess
import re
import sys
import time
import datetime
import gspread
#import csv
import RPi.GPIO as io
io.setmode(io.BCM)

# ===========================================================================
# Google Account Details
# ===========================================================================

# Account details for google docs
email       = 'g3rasppi@gmail.com'
password    = 'yoo3hooo'
spreadsheet = 'TempLog_v2'
errorsheet  = 'Errors'

# ===========================================================================
# Temperature and Humidity control using sensor readings to drive fridge and
# humidifier until values are reached with "hysteresis" band
# ===========================================================================

# Set Global Variables
sleeptimer = 3
humLo = 65
humHi = 70
tempLo = 55
tempHi = 60
hum_pin = 18
fridge_pin = 23
tempRange = []
humRange = []
counter = 0
login_counter = 0
#Setup IO direction
io.setwarnings(False)
io.setup(hum_pin, io.OUT)
io.setup(fridge_pin, io.OUT)
io.output(fridge_pin, False)
io.output(hum_pin, False)

# ============================================================================
# Define functions
# ============================================================================

# Function to average a range
def avg(seq):
	return sum(seq)/len(seq) 

# Function to log errors
def log_error():
	errorlog = gc.open(errorsheet)
	import traceback
  	errortxt = traceback.format_exc()
  	errorval = [datetime.datetime.now(), errortxt]
  	errorlog.sheet1.append_row(errorval)



# Function to set fridge_pin output
def fridge(TEMPVAL, TEMPHI, TEMPLO, FRIDGE_PIN):
	if (TEMPVAL >= TEMPHI):
        	io.output(FRIDGE_PIN, True)
	elif (TEMPVAL <= TEMPLO):
        	io.output(FRIDGE_PIN,False)

# Function to set fridge_pin output
def humidifier(HUMVAL, HUMHI, HUMLO, HUM_PIN):
        if (HUMVAL <= HUMLO):
                io.output(HUM_PIN, True)
        elif (HUMVAL >= HUMHI):
                io.output(HUM_PIN,False)
#=============================================================================

# Login with your Google account
try:
  gc = gspread.login(email, password)
except:
  print "Unable to log in.  Check your email address/password"
  sys.exit()

# Open a worksheet from your spreadsheet using the filename
try:
  ss = gc.open(spreadsheet)
  errorlog = gc.open(errorsheet)
  todaydate = unicode(datetime.date.today()) 
  worksheet = ss.worksheet(todaydate)

# If today's date worksheet is not found then create
except gspread.WorksheetNotFound:
  worksheet =  ss.add_worksheet(todaydate,1,5)
  colHeaders = ["Time/Date","Temp F","Humidity", "fridge_pin out", "hum_pin out"]
  worksheet.update_acell('A1', colHeaders[0])
  worksheet.update_acell('B1', colHeaders[1])
  worksheet.update_acell('C1', colHeaders[2])  
  worksheet.update_acell('D1', colHeaders[3])
  worksheet.update_acell('E1', colHeaders[4])


except:
  print "Unable to open the spreadsheet.  Check your filename: %s" % spreadsheet
  log_error()
  import traceback
  print traceback.format_exc()
 # continue
  #sys.exit()

# Continuously append data
while(True):
  # Login to google every 30 min or so, 300 cycles
  if (login_counter >= 300):
     try:
       gc = gspread.login(email, password)
       login_counter = 0
     except:
       print "Unable to open the spreadsheet.  Check your filename: %s" % spreadsheet
       log_error()
       import traceback
       print traceback.format_exc()
       continue

  # Run the DHT program to get the humidity and temperature readings!

  output = subprocess.check_output(["./Adafruit_DHT", "2302", "4"]);
  print output
  matches = re.search("Temp =\s+([0-9.]+)", output)
  if (not matches):
	time.sleep(3)
	continue
  temp = float(matches.group(1))
  temp = temp * 1.8 + 32

 
  # search for humidity printout
  matches = re.search("Hum =\s+([0-9.]+)", output)
  if (not matches):
	time.sleep(3)
	continue
  humidity = float(matches.group(1))

  print "Temperature: %.1f C" % temp
  print "Humidity:    %.1f %%" % humidity

  # Log and smooth out temp and hum readings 
  if ((temp < 90) & (temp > 30)):
  	tempRange.append(temp)
  if ((humidity < 100) & (humidity > 20)):
  	humRange.append(humidity)
  if (len(tempRange) > 5):
	tempRange.pop(0)
  if (len(humRange) > 5):
	humRange.pop(0)
  tempVal = avg(tempRange)
  humVal = avg(humRange)
  # Run the  humidifier function 
  if (io.input(fridge_pin)):
    humidifier(humVal, humHi+3, humLo, hum_pin)
  else:
    humidifier(humVal, humHi, humLo, hum_pin)

  # Run the fridge function
  fridge(tempVal, tempHi, tempLo, fridge_pin) 	
  	
  print "fridge pin = " + unicode(io.input(fridge_pin))
  print "hum pin = " +  unicode(io.input (hum_pin))
 # print len(tempRange)
 # print len(humRange)
 # logVal = [datetime.datetime.now(), temp, humidity,unicode(io.input (fridge_pin)),unicode(io.input (hum_pin))]
 # with open('log.csv', 'a') as csvlogger:
 #   writer = csv.writer(csvlogger)
 #   writer.writerow(logVal)
  counter = counter + 1
  login_counter = login_counter + 1
  # Append the data in the spreadsheet, including a timestamp
  try:
   todaydate = unicode(datetime.date.today())
   worksheet = ss.worksheet(todaydate) 
   values = [datetime.datetime.now(), tempVal, humVal,unicode(io.input (fridge_pin)),unicode(io.input (hum_pin))]
   if (counter > 5):
     worksheet.append_row(values)
     counter = 0
  # raise NameError('Butts')

  # If today's date worksheet is not found then create
  except gspread.WorksheetNotFound:
    todaydate = unicode(datetime.date.today())
    worksheet =  ss.add_worksheet(todaydate,1,5)
    colHeaders = ["Time/Date","Temp F","Humidity", "fridge_pin out", "hum_pin out"]
    worksheet.update_acell('A1', colHeaders[0])
    worksheet.update_acell('B1', colHeaders[1])
    worksheet.update_acell('C1', colHeaders[2])
    worksheet.update_acell('D1', colHeaders[3])
    worksheet.update_acell('E1', colHeaders[4])
    continue

  except:
    import traceback
    print "Unable to append data.  Check your connection?"
    log_error()
    continue
  # sys.exit()

  # Wait "sleeptimer" seconds before continuing
  print "Wrote a row to %s" % spreadsheet
  time.sleep(sleeptimer)
