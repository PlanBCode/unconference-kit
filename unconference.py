#!/usr/bin/env python

		#Gebruikerservaring:
		#(0) Bij opstarten kies je de locatie
		#(1) Als de tijd opkomt van het volgende praatje: knippert het scherm met deze info.
		#1a  Bevestigen met <OK/MENU> (lang)
		#1b als je een ander praatje wilt starten druk dan lang op UP of DOWN ==> menu met alle praatjes van het evenement (eerst van deze locatie, daarna de andere locaties) (navigatie met UP/DOWN, selecteren met <OK>
		#(2) Als praatje begint, begint ook het streamen (en ONAIR gaat aan)
		#(3) praatje eindigt automatisch na aantal minuten zoals in het schema staat. Praatje voortijdig stoppen met <OK/MENU> (lang).
		#(4) als het nog niet tijd is voor het volgende praatje (PAUZE)
		#terug naar 1

# DEBUG HINT
#      python ./unconference.py debug 201901271604


SCHEDULEURL="https://koppelting.org/huk.php?festival=meetkoppel19"	

STREAMME="/home/pi/streamme.sh %s"
STREAMURL="rtmp://136.144.128.49/show/"

discussion_minutes=10
timeIsUp = 30

import datetime
import sys
import pygame
import os
import time
import signal
import math
import threading
import platform
import schedule
import platform
import traceback

if  platform.machine()=='armv7l':
	from RPi import GPIO
	GPIO.setmode(GPIO.BCM)
	from rpi_ws281x import *
else:
	rpi_ws281x=None
	
import keyboard

fd=open("/tmp/unconference.pid",'w')
fd.write("%s"%os.getpid())
fd.close()

OK="enter"
UP="up"
DOWN="down"
keypressed=None
RED="100"
YELLOW="010"
GREEN="001"
BLANK="000"

ONAIR_LED_COUNT=20
PROGRESS_LED_COUNT=10

#TRAFFIC_LIGHT_LED_COUNT=56
# LED strip configuration:
LED_COUNT      = 2*PROGRESS_LED_COUNT+ONAIR_LED_COUNT      # Number of LED pixels.
LED_PIN        = 13   # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10 # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 1       # set to '1' for GPIOs 13, 19, 41, 45 or 53
lastCOL=None

global lastCOL
def lichtshow():
	print "STEP THROUGH THE TRAFFIC LIGHT"
	global goOn
	#while goOn:
	if goOn:
		#OnAir(True)
		time.sleep(1)

		for i in range(10):
			ProgressBar(i*10,-1) #0/PROGRESS_LED_COUNT)
			time.sleep(0.1)	

def ProgressBar(percent,col=None):
	#print "ProgressBar:",percent,col
	global lastCOL
	if (col,percent/10)==lastCOL:
		return
	
	if col==RED:
		color=Color(255,0,0)
	elif col==YELLOW:
		color=color=Color(128,128,0)
	elif col==GREEN:
		color=color=Color(0,255,0)		
	elif col==-1:
		color=color=Color(0,0,255)
	else:
		color=Color(0,0,0)
	for i in range(PROGRESS_LED_COUNT):
		if i<=percent/10: #TODO get the value from PROGRESS_LED_COUNT, I am too lazy right now to make a good formula for that
			strip.setPixelColor(ONAIR_LED_COUNT+i, color)
			#strip.setPixelColor(ONAIR_LED_COUNT+PROGRESS_LED_COUNT+i, color)
		else:
			strip.setPixelColor(ONAIR_LED_COUNT+i, Color(0,0,0))
			#strip.setPixelColor(ONAIR_LED_COUNT+PROGRESS_LED_COUNT+i, Color(0,0,0))		
	strip.show()
	lastCOL=(col,percent/10)


# Create NeoPixel object with appropriate configuration.
if platform.machine()=='armv7l':
	strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
	# Intialize the library (must be called once before other functions).
	strip.begin()
	global goOn	
	if platform.machine() == 'armv7l': 	
		goOn=True
		thread=threading.Thread(target=lichtshow)
		thread.start()	
else:
	class DummyRGB():
		def show(self):
			return
		def setPixelColor(self,i,col):
			return
		def numPixels(self):
			return 3
	class Color():
		def __init__(self,r,g,b):
			return None
		
	strip=DummyRGB()
	
def colorWipe(strip, color):
	"""Wipe color across display a pixel at a time."""
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, color)
	strip.show()


#ROTARY ENCODER
clk = 8
dt = 25
sw= 7

	
def my_callback(channel):  
	#global clkLastState
	#global counter
	global keypressed
	try:
		clkState = GPIO.input(clk)
		dtState = GPIO.input(dt)

		print ">",clkState,dtState
		#if clkState != clkLastState:
		if 1:	
			if dtState != clkState:
				#counter += 1
				keypressed=UP
			else:
				#counter -= 1
				keypressed=DOWN
			#print "@",counter
			
		#clkLastState = clkState
		time.sleep(0.01)
	except:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
		print ''.join('!! ' + line for line in lines)  # Log it or whatever here
		pass

def my_btn(channel):
	global keypressed
	print "BTN!"	
	keypressed=OK
if  platform.machine()=='armv7l':
	GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(sw, GPIO.IN, pull_up_down=GPIO.PUD_UP)	
	GPIO.add_event_detect(clk, GPIO.FALLING  , callback=my_callback, bouncetime=300)  
	GPIO.add_event_detect(sw, GPIO.FALLING  , callback=my_btn, bouncetime=300)  	
	
	
colorWipe(strip, Color(0,0,0))

pygame.init()
white = (255, 255, 255) 
black=(0,0,0)
global timedelta
timedelta=0

print "SYS.ARGV=",sys.argv
BASEDIR=""
while not BASEDIR:
	fd=open("/proc/mounts")
	lines=fd.readlines()
	fd.close()
	
	for l in lines:
		parts=l.split(" ")
		if parts[0]=="/dev/sda1":
			BASEDIR=parts[1].replace("\\040"," ")
			break
	if not BASEDIR:
		background = pygame.Surface(screen.get_size())
		background = background.convert()
		background.fill(black)
		screen.blit(background, (0, 0))				
		font2 = pygame.font.Font('freesansbold.ttf', 32) 
		text2 = font2.render("PLUG IN USB STICK FOR CONFIGURATION AND STORAGE OF THE TALKS", True, white, black) 
		textRect2 = text2.get_rect()  
		textRect2.center = (width // 2, height-80) 				
		screen.blit(text2, textRect2)
		pygame.display.flip()
		time.sleep(3)
		sys.exit()

#BASEDIR=sys.argv[1].replace("\\040"," ")

#print "BASEDIR=",BASEDIR
RECORDTARGET="rtmp://123.123.123.123/show/"
DONTRECORD=False

configtxt="""
# this is the config file for the unconference system

#enter the URL for your event here. 
SCHEDULEURL="https://koppelting.org/huk.php?festival=meetkoppel19"

#see this example URL for the format that is expected

#change the wifi network here if your network is different.
#TIP: make the network for the unconference boxes different from the participant network as you do not want the participants block the streaming bandwidth!

WIFI_SSID="unconferencekit"
WIFI_PSK="YnqEeKSUJZ6tWQQ9"
WIFI_KEYMGMT=WPA-PSK

#you will find the recordings made in the Recordings directory created on this stick
#If you do NOT want the recordings to be made uncomment the below file
#DONTRECORD=True

#replace this with your own rtmp target. The location name (from the schedule) will be added to the end of this URL for the upload.
#RECORDTARGET=rtmp://123.123.123.123/show/ 
#uncomment the line below to disable streaming alltogether
#RECORDTARGET=

"""

def readconfig():
	try:
		fd=open(BASEDIR+"/config.txt")
		lines=fd.readlines()
		fd.close()
		ssid=None
		psk=None
		keymgmt="WPA-PSK"
		for l in lines:
			if l[0]!="#" and l.strip():
				try:
					field,val=l.strip().split("=")
					if field=="SCHEDULEURL":
						global SCHEDULEURL
						SCHEDULEURL=val.strip()[1:-1]
						print "SCHEDULEURL:",SCHEDULEURL
					elif field=="DONTRECORD" and val.strip()=="True":
						os.system("sudo umount "+BASEDIR)
					elif field=="RECORDTARGET":
						global STREAMURL
						STREAMURL=val.strip()
					elif field=="WIFI_SSID":
						ssid=val.strip()[1:-1]
					elif field=="WIFI_PSK":
						psk=val.strip()[1:-1]
					elif field=="WIFI_KEYMGMT":
						keymgmt=val.strip()

				except:
					pass
		if ssid and psk:
			#first test if this wifi network is already known
			fd2=open("/etc/wpa_supplicant/wpa_supplicant.conf")
			wpalines=fd2.readlines()
			fd2.close()
			for w in range(len(wpalines)-3):
				#print 'ssid="%s"'%ssid,'psk="%s"'%psk,'key_mgmt=%s'%keymgmt
				#print w,wpalines[w].find('ssid="%s"'%ssid),wpalines[w+1].find('psk="%s"'%psk), wpalines[w+2].find('key_mgmt=%s'%keymgmt)
				if wpalines[w].find('ssid="%s"'%ssid)>=0 and \
					wpalines[w+1].find('psk="%s"'%psk)>=0 and \
					wpalines[w+2].find('key_mgmt=%s'%keymgmt)>=0:
					ssid=None
					break
				if not ssid: break
			if ssid:
				#not configured
				netw="""

network={
        ssid="%s"
        psk="%s"
        key_mgmt=%s
}

"""%(ssid,psk,keymgmt)				
				os.system("echo '%s' | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf"%netw)


	except IOError:
		print "No config.txt found, writing a template one"
		try:
			fd=open(BASEDIR+"/config.txt",'w')
			fd.write(configtxt)
			fd.close()
		except IOError:
			RECORDTARGET=""
			pass

readconfig()	
sched=schedule.schedule(SCHEDULEURL)

try:
	i=sys.argv.index("debug")
	if i>0:
		TODAY=sys.argv[i+1][4:6]+"-"+sys.argv[i+1][6:8]
		sched.setday(TODAY)
		timestamp=time.mktime(datetime.datetime.strptime(sys.argv[i+1], "%Y%m%d%H%M").timetuple())

		timedelta=time.time()-timestamp
except ValueError:
	pass
def now():
	return time.time()-timedelta

def callback(event):
	#print event
	name=event.name
	global keypressed
	if name in [OK, UP, DOWN]:	keypressed=name	
	elif name=="help": keypressed=DOWN
	elif name=="f13": keypressed=OK
	elif name=="f14": keypressed=UP
				
keyboard.on_press(callback)

def waitOK(wait=None):
	btn=None
	global keypressed
	t=time.time()
	while not keypressed:
		time.sleep(.1)
	print "waitok", keypressed
	while keypressed!=OK and (time.time()-t)<30:
		time.sleep(0.1)
	if not wait:	
		if keypressed==OK:
			keypressed=None
			return True
	while keypressed==OK and wait>0:
		time.sleep(.2)
		wait-=.2
	if wait<=0: #the timer ran out	
		keypressed=None
		return True
	keypressed=None
	return False

def demoMode():
	global sched
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	background.fill((200,0,0))
	screen.blit(background, (0, 0))
	font = pygame.font.Font('freesansbold.ttf', 40) 	
	text = font.render("No (further) events on this location today!!", True, white, (255,0,0)) 
	textRect = text.get_rect()  
	textRect.center = (width // 2, height-140) 
	screen.blit(text, textRect)
	font = pygame.font.Font('freesansbold.ttf', 24) 	
	text = font.render("Press and HOLD the BUTTON for a demo.", True, white, (0,0,0)) 
	textRect = text.get_rect()  
	textRect.center = (width // 2, height-40) 
	screen.blit(text, textRect)
	pygame.display.flip()
	if waitOK(3):
		print "***** GOT OK, going to DEMO mode *******"
		background.fill(black)
		screen.blit(background, (0, 0))
	
		font = pygame.font.Font('freesansbold.ttf', 40) 	
		text = font.render("LOADING DEMO SCHEDULE", True, white, (0,0,255)) 
		textRect = text.get_rect()  
		textRect.center = (width // 2, 20) 
		screen.blit(text, textRect)
		pygame.display.flip()
	
		SCHEDULEURL="https://koppelting.org/huk.php?festival=meetkoppel19"
		sched=schedule.schedule(SCHEDULEURL)
		#location=sched.getlocationnum()
		sched.setlocation(0)
		aa="201901271604"
		i=len(sys.argv)-1
		sys.argv.append(aa)
		TODAY=sys.argv[i+1][4:6]+"-"+sys.argv[i+1][6:8]
		print "TODAY=",TODAY
		sched.setday(TODAY)
		global timestamp
		timestamp=time.mktime(datetime.datetime.strptime(sys.argv[i+1], "%Y%m%d%H%M").timetuple())
		global timedelta
		timedelta=time.time()-timestamp
		return True
	else:	
		return None


if platform.machine() != 'armv7l':
	#sched.setlocation(-1)
	#print sched.getlocation()
	screen = pygame.display.set_mode((1280,640)   )            #(0, 0), pygame.FULLSCREEN, 32)
else:	
	screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, 32)

width, height = pygame.display.Info().current_w, pygame.display.Info().current_h

def testbeeld():
	streamurl=STREAMURL+sched.getlocation()
	print "STREAMURL=",streamurl
	os.system("/home/pi/testbeeld.sh %s"%streamurl)

def textselector(lst, index):
	for i in range(len(lst)):
		font = pygame.font.Font('freesansbold.ttf', 32) 
		if i==index:
			a,b=black,white
		else:
			a,b=white, black
		text = font.render(lst[i], True, a,b) 
		textRect = text.get_rect()  
		textRect.center = (width // 2, 100+40*i) 
		screen.blit(text, textRect)

def waitbutton(dontwait=None, holdme=None):
	print "waitbutton", dontwait, holdme	
	global keypressed
	print "1", keypressed
	if dontwait and keypressed: return None
		
	while not keypressed:
		time.sleep(.1)

	print "2", keypressed
	val=keypressed
	keypressed=None
	return val


def locationmenu():
	print "locationsmenu:",
	locations=sched.getlocations()
	print locations
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	background.fill(black)
	screen.blit(background, (0, 0))

	font = pygame.font.Font('freesansbold.ttf', 40) 	
	text = font.render("Indicate location we are in. Use ROTATE the knob and select by pressing it", True, white, (0,0,255)) 
	textRect = text.get_rect()  
	textRect.center = (width // 2, 20) 
	screen.blit(text, textRect)

	goon=True
	index=0
	while goon:
		textselector(locations,index)
		pygame.display.flip()
		btn=waitbutton()
		if btn==OK: return index
		elif btn==DOWN:
			index+=1
			if index>=len(locations):
				index=0
		elif btn==UP:
			index-=1
			if index<0:
				index=len(locations)-1

def waitnobuttonspressed():
	while keypressed:
		time.sleep(0.1)
		
##
##RED_RANGE=[TRAFFIC_LIGHT_LED_COUNT-(TRAFFIC_LIGHT_LED_COUNT/3), TRAFFIC_LIGHT_LED_COUNT]		
##YELLOW_RANGE=[(TRAFFIC_LIGHT_LED_COUNT/3)+1,2*(TRAFFIC_LIGHT_LED_COUNT/3)]
##GREEN_RANGE=[0,(TRAFFIC_LIGHT_LED_COUNT/3)]
##
##
##print "RED=", RED_RANGE
##print "YELLOW=", YELLOW_RANGE
##print "GREEN=", GREEN_RANGE




def OnAir(val):
	print "ONAIR=",val
	global doorgaan
	if platform.machine()=="armv7l": 
		if val:
			#val=GPIO.HIGH
			color=Color(255,0,0)
		else:
			#val=GPIO.LOW
			color=Color(0,0,0)
		for i in range(ONAIR_LED_COUNT):
			strip.setPixelColor(i, color)
		strip.show()	

global doorgaan
doorgaan=True

def blinker():
	while doorgaan:
		OnAir(True)
		time.sleep(.2)
		OnAir(False)
		time.sleep(.2)
		

def clearscreen():
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	background.fill(black)
	screen.blit(background, (0, 0))
	pygame.display.flip()
	pygame.mouse.set_visible(0)

def preview():
	os.system("killall picam")
	clearscreen()
	os.system("/home/pi/preview.sh")	
	waitOK()
	os.system("killall raspivid")	

def showtalkmenu(location=None,day=None):
	print "showtalkmenu:", location,day
	days=sched.otherdays(day)
	if not location:
		location=sched.getlocation()	
	locations=sched.otherlocations(location)
	t=sched.gettalks(location,day)
	offset=1
	talks=["<<< back to current talk"]
	for i in locations:
		talks.append(">>> to location:"+i.upper())
		offset+=1
	for i in days:
		talks.append(">>> to day:"+i)
		offset+=1		
	talks.append(">>> preview mode")
	offset+=1	
	for title,duration in t:
		talks.append(title)
	print talks
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	background.fill(black)
	screen.blit(background, (0, 0))
	font = pygame.font.Font('freesansbold.ttf', 40) 	
	text = font.render("Select different talk to start or go back to current talk", True, white, (0,0,255)) 
	textRect = text.get_rect()  
	textRect.center = (width // 2, 20) 
	screen.blit(text, textRect)
	pygame.display.flip()
	waitnobuttonspressed()
	goon=True
	index=0
	while goon:
		textselector(talks,index)
		pygame.display.flip()
		btn=waitbutton()
		if btn==OK:
			print "index=",index
			if index>=offset:
				talk,duration=t[index-offset]
				return talk[6:], duration
			elif index==0:
				raise NameError()
			elif index<=len(locations):
				location=locations[index-1]
				a,b=showtalkmenu(location,day)
				return a,b
			elif index==offset-1:
				preview()
			else:
				day=days[index-1-len(locations)]
		elif btn==DOWN:
			index+=1
			if index>=len(talks):
				index=0
		elif btn==UP:
			index-=1
			if index<0:
				index=len(talks)-1

digit_hash = {}
digit_hash[0] = int('1110111', 2)
digit_hash[1] = int('0100100', 2)
digit_hash[2] = int('1011101', 2)
digit_hash[3] = int('1101101', 2)
digit_hash[4] = int('0101110', 2)
digit_hash[5] = int('1101011', 2)
digit_hash[6] = int('1111011', 2)
digit_hash[7] = int('0100101', 2)
digit_hash[8] = int('1111111', 2)
digit_hash[9] = int('0101111', 2)

led_width=width/7.5
led_height=led_width/7
top_offset = 10
left_offset = 10
#led_height = 15
#led_width = 100

offset = 4 * led_height / 3

digit_width = 2*offset + led_width
digit_height = 4*offset + 2*led_width

fir_min_dig = pygame.Surface((digit_width, digit_height))
sec_min_dig = pygame.Surface((digit_width, digit_height))
fir_sec_dig = pygame.Surface((digit_width, digit_height))
sec_sec_dig = pygame.Surface((digit_width, digit_height))
digit_colour = pygame.Color(0, 255, 0)

def draw_digit(canvas, color, digit,drawminus=None):
	mask = digit_hash[digit]

	# Top Center
	if(mask & int('0000001', 2)):
		pygame.draw.rect(canvas, color, pygame.Rect(offset, 0, led_width, led_height))
	# Top Left
	if(mask & int('0000010', 2)):
		pygame.draw.rect(canvas, color, pygame.Rect(0, offset, led_height, led_width))
	# Top Right
	if(mask & int('0000100', 2)):
		pygame.draw.rect(canvas, color, pygame.Rect(2*offset + led_width - led_height, offset, led_height, led_width))
	# Middle Center
	if drawminus or (mask & int('0001000', 2)):
		pygame.draw.rect(canvas, color, pygame.Rect(offset, 2*offset + led_width - led_height, led_width, led_height))
	# Bottom Left
	if(mask & int('0010000', 2)):
		pygame.draw.rect(canvas, color, pygame.Rect(0, 3*offset + led_width - led_height, led_height, led_width))
	# Bottom Right
	if(mask & int('0100000', 2)):
		pygame.draw.rect(canvas, color, pygame.Rect(2*offset + led_width - led_height, 3*offset + led_width - led_height, led_height, led_width))
	# Bottom Center
	if(mask & int('1000000', 2)):
		pygame.draw.rect(canvas, color, pygame.Rect(offset, 4*offset + 2*led_width - 2*led_height, led_width, led_height))

def draw_time(screen, total_seconds):
	if total_seconds<0:
		total_seconds=-total_seconds
		drawminus=True
	else:
		drawminus=False
	sec = int(total_seconds % 60)
	min = int(math.floor(total_seconds / 60))

	fir_min = int(math.floor(min / 10))
	sec_min = int(min % 10)

	fir_sec = int(math.floor(sec / 10))
	sec_sec = int(sec % 10)

	fir_min_dig.fill(black)
	draw_digit(fir_min_dig, digit_colour, fir_min, drawminus)
	screen.blit(fir_min_dig, (left_offset, top_offset))

	sec_min_dig.fill(black)
	draw_digit(sec_min_dig, digit_colour, sec_min)
	screen.blit(sec_min_dig, (left_offset + 2*offset + digit_width, top_offset))

	fir_sec_dig.fill(black)
	draw_digit(fir_sec_dig, digit_colour, fir_sec)
	screen.blit(fir_sec_dig, (left_offset + 2*(2*offset + digit_width) + 2*offset + led_height, top_offset))

	sec_sec_dig.fill(black)
	draw_digit(sec_sec_dig, digit_colour, sec_sec)
	screen.blit(sec_sec_dig, (left_offset + 3*(2*offset + digit_width) + 2*offset + led_height, top_offset))



	
class buttonpressed(Exception): 
	def __init__(self,val):
		self.val=val

def waitforbutton(timeout=1):
	#print "waitforbutton", timeout
	t=time.time()
	lastpress=None
	global keypressed
	while time.time()<(t+timeout) and not keypressed: 
			time.sleep(.1)
	#print "22",		keypressed
	if	keypressed:
		btn=keypressed
		keypressed=None
		raise buttonpressed(btn)
	keypressed=None

def showcountdown(lecture_seconds, text):
	print "SHOWCOUNTOUN. seconds=",lecture_seconds, text
	
	#Stoplicht(None)
	ProgressBar(0)
	
	OnAir(False)
	global digit_colour
	digit_colour = pygame.Color(0, 0, 255)
	# Fill background
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	background.fill(black)
	screen.blit(background, (0, 0))

	font = pygame.font.Font('freesansbold.ttf', 32) 
	text = font.render(text, True, white, black) 
	textRect = text.get_rect()  
	textRect.center = (width // 2, height-40) 
	screen.blit(text, textRect)

	font2 = pygame.font.Font('freesansbold.ttf', 32) 
	text2 = font2.render("Press BUTTON to start, ROTATE to select other talk", True, white, black) 
	textRect2 = text2.get_rect()  
	textRect2.center = (width // 2, height-80) 

	# Colon between minutes and seconds
	pygame.draw.rect(screen, digit_colour, pygame.Rect(left_offset + 2*(2*offset + digit_width), top_offset + offset + led_width / 2 - led_height, led_height, led_height))
	pygame.draw.rect(screen, digit_colour, pygame.Rect(left_offset + 2*(2*offset + digit_width), top_offset + 3*offset + 3 * led_width / 2 - led_height, led_height, led_height))
	i=-lecture_seconds 
	# Draw time on screen
	while i<0:
		draw_time(screen, -i)
		pygame.display.flip()
		waitforbutton()
		i+=1
	while True:
		#blinkyblink
		#print "LOOP3"
		draw_time(screen, 0)
		pygame.display.flip()
		waitforbutton()	
		screen.blit(background, (0, 0))
		screen.blit(text, textRect)
		screen.blit(text2, textRect2)
		pygame.display.flip()
		waitforbutton()	

def showtimer(lecture_seconds, text):
	print "SHOWTIMER:",lecture_seconds,text
	# Initialize screen
	#Stoplicht(GREEN)
	global digit_colour
	digit_colour = pygame.Color(0, 255, 0)
	# Fill background
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	background.fill(black)
	screen.blit(background, (0, 0))

	font = pygame.font.Font('freesansbold.ttf', 32) 
	label = font.render(text, True, white, black) 
	textRect = label.get_rect()  
	textRect.center = (width // 2, height-40) 
	screen.blit(label, textRect)

	# Colon between minutes and seconds
	pygame.draw.rect(screen, digit_colour, pygame.Rect(left_offset + 2*(2*offset + digit_width), top_offset + offset + led_width / 2 - led_height, led_height, led_height))
	pygame.draw.rect(screen, digit_colour, pygame.Rect(left_offset + 2*(2*offset + digit_width), top_offset + 3*offset + 3 * led_width / 2 - led_height, led_height, led_height))

	for i in range(-lecture_seconds, -discussion_minutes*60, 1):
		ProgressBar(10+int((100*(i+lecture_seconds))/float(lecture_seconds)), GREEN)
		            
		# Draw time on screen
		draw_time(screen, -i)
		#print "Lecture:",int(-i/60),(lecture_seconds-i)%60
		pygame.display.flip()
		try:
			waitforbutton()
		except buttonpressed as inst:
			btn=inst.val
			if btn!=OK: raise buttonpressed(btn)
			else:
				#PAUZE!
				background = pygame.Surface(screen.get_size())
				background = background.convert()
				background.fill(black)
				screen.blit(background, (0, 0))				
				font2 = pygame.font.Font('freesansbold.ttf', 32) 
				text2 = font2.render("Press BUTTON to continue, ROTATE to select other talk", True, white, black) 
				font3 = pygame.font.Font('freesansbold.ttf', 32) 
				text3 = font2.render("Session paused, Streaming is STOPPED.", True, white, black) 
				textRect2 = text2.get_rect()  
				textRect2.center = (width // 2, height-80) 				
				screen.blit(text2, textRect2)
				textRect3 = text3.get_rect()  
				textRect3.center = (width // 2, height-120) 				
				screen.blit(text3, textRect3)
				pygame.display.flip()

				stopsession(True)
				
				btn=waitbutton()	
				if btn!=OK:
						raise buttonpressed(btn)
				
				startsession()
					
				background = pygame.Surface(screen.get_size())
				background = background.convert()
				background.fill(black)
				screen.blit(background, (0, 0))					
				font = pygame.font.Font('freesansbold.ttf', 32) 
				label = font.render(text, True, white, black) 
				textRect = label.get_rect()  
				textRect.center = (width // 2, height-40) 
				screen.blit(label, textRect)				
	digit_colour = pygame.Color(255, 150, 0)

	# Colon between minutes and seconds
	pygame.draw.rect(screen, digit_colour, pygame.Rect(left_offset + 2*(2*offset + digit_width), top_offset + offset + led_width / 2 - led_height, led_height, led_height))
	pygame.draw.rect(screen, digit_colour, pygame.Rect(left_offset + 2*(2*offset + digit_width), top_offset + 3*offset + 3 * led_width / 2 - led_height, led_height, led_height))

	#Stoplicht(YELLOW)
	ProgressBar(80,YELLOW)

	for k in range(-discussion_minutes*60,-2*timeIsUp, 1):
		# Draw time on screen
		draw_time(screen, -k)
		if k==-discussion_minutes*60/2:
			ProgressBar(90,YELLOW)
		#print "Discussion:",int(-k/60),(discussion_seconds-k)%60
		pygame.display.flip()
		waitforbutton()

	digit_colour = pygame.Color(255, 0, 0)

	# Colon between minutes and seconds
	pygame.draw.rect(screen, digit_colour, pygame.Rect(left_offset + 2*(2*offset + digit_width), top_offset + offset + led_width / 2 - led_height, led_height, led_height))
	pygame.draw.rect(screen, digit_colour, pygame.Rect(left_offset + 2*(2*offset + digit_width), top_offset + 3*offset + 3 * led_width / 2 - led_height, led_height, led_height))

	print "Time is up!"
	#Stoplicht(RED)
	ProgressBar(100,RED)

	for j in range(0, timeIsUp):
		# Draw time on screen
		digit_colour = pygame.Color(255, 0, 0)

		draw_time(screen, 0)
		pygame.display.flip()
		waitforbutton()

		digit_colour = pygame.Color(0, 0, 0)

		draw_time(screen, 0)
		pygame.display.flip()
		waitforbutton()


def startsession():
	background = pygame.Surface(screen.get_size())
	background = background.convert()
	background.fill(black)
	screen.blit(background, (0, 0))
	
	font = pygame.font.Font('freesansbold.ttf', 32) 
	label = font.render("Starting the stream&recording, please wait a moment...", True, white, black) 
	textRect = label.get_rect()  
	textRect.center = (width // 2, height-40) 
	screen.blit(label, textRect)
	pygame.display.flip()
	
	stopsession(True)
	global doorgaan	
	doorgaan=True	
	blinkthread=threading.Thread(target=blinker)
	blinkthread.start()	
	if platform.machine()=="armv7l": 
		if STREAMURL:	
			os.system(STREAMME%(STREAMURL+sched.getlocation()))
		else:
			os.system(STREAMME%(""))
		#start recording and set the presentation title in the image
		fd=open("subtitle",'w')
		fd.write("duration=30\nlayout_align=top,center\ntext=%s\n"%bezig)
		fd.close()
		os.system("touch hooks/start_record")
		os.system("cp subtitle hooks/subtitle")
	else:
		print "NOT STARTING STREAMING"
		time.sleep(3)
	doorgaan=None
	blinkthread.join()	
	OnAir(True)
		
def stopsession(notestbeeld=None):
	#stop the recording
	
	if platform.machine()=="armv7l": 
		os.system("touch hooks/stop_record")
		time.sleep(1)
		os.system("killall picam")
		OnAir(False)	
		if not notestbeeld:
			testbeeld()
		time.sleep(2)
	

def doSession(currentTitle,duration,presenter):
	if not presenter and currentTitle: bezig=currentTitle
	elif presenter and not currentTitle: bezig=presenter
	elif presenter and currentTitle:	bezig=presenter+" - "+currentTitle
	else: bezig=""

	startsession()
	
	showtimer(int(duration),bezig)
	stopsession(True)		
	
print "PROBING SCHEDULE"	  
currentTitle,duration,presenter, padme=sched.nextup(now())
if currentTitle==None:
	print demoMode()

print "ARGV now=", sys.argv
##			currentTitle,duration,presenter, padme=sched.nextup(now()	

if platform.machine() == 'armv7l': 	#raspi
	#from pixels import Pixels
	#pixels = Pixels()
	#pixels.off()
	
	preview()
	
	##	Stoplicht(RED)
	##	time.sleep(1)
	##	Stoplicht(YELLOW)
	##	time.sleep(1)
	##	Stoplicht(GREEN)
	##	time.sleep(1)
	##	Stoplicht(BLANK)
	goOn=False
	thread.join()
	ProgressBar(0,BLANK)
	OnAir(False)

	

index=locationmenu()
print "LOCATIONMENU RETURNED:",index
sched.setlocation(index)
testbeeld() #starts the testbeeld.sh script 
#clear the screen
background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill(black)
screen.blit(background, (0, 0))
font = pygame.font.Font('freesansbold.ttf', 32) 
text = font.render(".....getting schedule for %s...."%sched.getlocation(), True, white, black) 
textRect = text.get_rect()  
textRect.center = (width // 2, height-40) 
screen.blit(text, textRect)
pygame.display.flip()	
	
bezig=""


while 1:
	clearscreen()
	#Stoplicht(BLANK)
	ProgressBar(0, BLANK)
	OnAir(False)
	waitnobuttonspressed()
	global lecture_minutes
	#read the schedule
	index=-1
	st0=time.time()
	print "START READING SCHEDULE"	  
	currentTitle,duration,presenter, padme=sched.nextup(now())
	print currentTitle,duration,presenter, padme
	if currentTitle==None:
		if demoMode(): #we should not get here....
			currentTitle,duration,presenter, padme=sched.nextup(now())
		else:	
			break	

	print "DONE READING SCHEDULE after %s, seconds"%(int(time.time()-st0))
	print currentTitle,duration,presenter, padme
	index=0
	laststart=None
	while True:
		try:
			print "LOOP duration:", duration, laststart
			#if duration<0:
			try:
				showcountdown(0,currentTitle)
			except buttonpressed as inst:
					print "ButtonPRESSED2",
					#btn=waitbutton(True,1)
					btn=inst.val
					print "btn=",btn
					if btn!=OK:
						raise
			#else:
##				try:
##					if not laststart:
##						showcountdown(0,currentTitle)
##				except buttonpressed as inst:
##					#print "ButtonPRESSED2",
##					#btn=waitbutton(True,1)
##					btn=inst.val
##					#print "btn=",btn
##					if btn!=OK:
##						raise
			laststart=now()
			doSession(currentTitle,duration,presenter)
			currentTitle,duration,presenter, padme=sched.nextup(now())
		except buttonpressed as inst:
			print "ButtonPRESSED1",
			btn=inst.val
			print "btn1=",btn			
			#btn=waitbutton(True,1)
			#print btn
			if btn  in [UP,DOWN]:
				if laststart:
					duration-=(now()-laststart)
				try:
					currentTitle, duration=showtalkmenu()
					presenter=''
				except NameError:
					pass
				print "New title=",currentTitle, duration
			elif btn == OK:
				#this should give us the start of the next session
				currentTitle,duration,presenter, padme=sched.nextup(now()) #+1 just to make sure we do not have any rounding issues
