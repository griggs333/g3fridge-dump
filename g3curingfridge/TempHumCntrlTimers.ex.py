#!/usr/bin/python

import subprocess
import re
import sys
import time
import datetime
import gspread
import RPi.GPIO as io
io.setmode(io.BCM)

# ===========================================================================
# Google Account Details
# ===========================================================================

# Account details for google docs
email       = 'g3rasppi@gmail.com'
# password    = '*****' removed for privacy
spreadsheet = 'TempLog'
errorsheet  = 'Errors'

# ===========================================================================
# Example Code
# ===========================================================================

# Set Global Variables
sleeptimer = 1
humLo = 50
tempHi = 70
fridgetimer = 30
humtimer = 60
hum_pin = 18
fridge_pin = 23

#Setup IO direction
io.setup(hum_pin, io.OUT)
io.setup(fridge_pin, io.OUT)
io.output(fridge_pin, False)
io.output(hum_pin, False)

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
 # raise NameError('works?')

# If today's date worksheet is not found then create
except gspread.WorksheetNotFound:
  worksheet =  ss.add_worksheet(todaydate,1,3)
  colHeaders = ["Time/Date","Temp F","Humidity"]
  worksheet.update_acell('A1', colHeaders[0])
  worksheet.update_acell('B1', colHeaders[1])
  worksheet.update_acell('C1', colHeaders[2])  

except:
  print "Unable to open the spreadsheet.  Check your filename: %s" % spreadsheet
  import traceback
  errortxt = traceback.format_exc()
  errorval = [datetime.datetime.now(), errortxt]
  errorlog.sheet1.append_row(errorval) 
  import traceback
  print traceback.format_exc()
 # continue
  #sys.exit()

# Continuously append data
while(True):
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
 
# Run the  humidifier if humidity drops below "humLo" low humidity setpoint 
  if (humidity < humLo):
  	io.output(hum_pin, True)
	print 'Humidifier On'
  	time.sleep(humtimer)
  	io.output(hum_pin, False)
  	
  #
  # Append the data in the spreadsheet, including a timestamp
  try:
   worksheet = ss.worksheet(todaydate) 
   values = [datetime.datetime.now(), temp, humidity]
   worksheet.append_row(values)
  # raise NameError('Butts')

  # If today's date worksheet is not found then create
  except gspread.WorksheetNotFound:
    todaydate = unicode(datetime.date.today())
    worksheet =  ss.add_worksheet(todaydate,1,3)  
    colHeaders = ["Time/Date","Temp F","Humidity"]
    worksheet.update_acell('A1', colHeaders[0])
    worksheet.update_acell('B1', colHeaders[1])
    worksheet.update_acell('C1', colHeaders[2])
    continue

  except:
    import traceback
    print "Unable to append data.  Check your connection?"
    errortxt = traceback.format_exc()
    errorval = [datetime.datetime.now(), errortxt]
    errorlog.sheet1.append_row(errorval)
    time.sleep(30)
    continue
  # sys.exit()

  # Wait 30 seconds before continuing
  print "Wrote a row to %s" % spreadsheet
  time.sleep(sleeptimer)
