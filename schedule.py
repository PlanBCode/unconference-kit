import urllib2, json, time, datetime

class schedule:
	def __init__(self,url):
		print "NEWSCHEDULE URL=",url
		self.myurl=url
		self.mylocation=0
		self.today=time.strftime('%m-%d') 
		self.reloadschedule()
		
	def setday(self, day):
		self.today=day

	def reloadschedule(self):
		print "RELOADSCHEDULE"
		file = urllib2.urlopen(self.myurl)
		data = file.read()
		file.close()

		self.data = json.loads(data)
		days=[]
		locations=[]
		for d in self.data:
			l=d['location']
			if l not in locations:
				locations.append(l)  
			sday=d['datetime'][4:6]+"-"+d['datetime'][6:8]
			if sday not in days: days.append(sday)
		locations.sort()        
		days.sort()
		self.locations=locations
		self.days=days

	def getlocations(self):
		return self.locations
	
	def otherlocations(self, location=None):
		if not location: location=self.mylocation
		lst=[]
		for l in self.locations:
			if l!=location: lst.append(l)
		lst.sort()
		return lst
	
	def otherdays(self, day=None):
		if not day: day=self.today
		
		lst=[]
		for d in self.days:
			if d!=day:
				lst.append(d)
		lst.sort()
		return lst
	
	def getdays(self):
		return self.days
	
	def getlocation(self):
		return self.locations[self.mylocation]
		
	def getlocationnum(self):
		return self.mylocation

	def setlocation(self, locnum):
		print "setlocation:",locnum,
		self.mylocation=locnum
		print "==",self.locations[self.mylocation]
		
	def gettalks(self,location=None,day=None):
		if not day:
			day=self.today
		elif day not in self.days: raise ValueError("wrong day. %s not in %s"%(day, self.days))	
		if not location:
			location=self.mylocation
		elif location not in self.locations: raise ValueError("wrong location. %s not in %s"%(location, self.locations))	
		try:
			self.reloadschedule()
		except:
			pass
		talks=[]
		for d in self.data:
			if d['location']==location:
				time=d['datetime'][-4:]
				sday=d['datetime'][4:6]+"-"+d['datetime'][6:8]
				if day==sday:
					line=time[:2]+":"+time[-2:]+" "+d['name'][:20]+" - "+d['title'][:30]
					talks.append((line, 60*int(d['duration'])))
		talks.sort()
		print "returning:",talks
		return talks

	def nextup(self,t=time.time()):
		print "NEXTUP, ",t
		try:
			self.reloadschedule()
		except:
			print "something went wrong with reload schedule"
			pass
		nexttalk=None
		for d in self.data:
			#print "==>",d['location']
			if d['location']==self.locations[self.mylocation]:
				start=time.mktime(datetime.datetime.strptime(d['datetime'], "%Y%m%d%H%M").timetuple())
				duration=int(d['duration'])*60
				if (t>=start) and (t<=start+duration):
                                        nexttalk = (start, d)
                                        break
                                if start>t and (not nexttalk or start < nexttalk[0]):
                                        nexttalk = (start, d)
		if nexttalk==None:
			return None,None,None,None
		else:
                        start, d = nexttalk
                        return d['title'], d['duration']*60, d['name'], d['padname']

if __name__ == '__main__':
	SCHEDULEURL="https://koppelting.org/huk.php?festival=meetkoppel19"
	sched= schedule(SCHEDULEURL)
	print sched.getlocations()
	sched.setlocation(1)
	print sched.getlocation()
	t=sched.gettalks()
	st0=time.time()
	print "START READING SCHEDULE"	  

	print sched.nextup(time.mktime(datetime.datetime.strptime('201901271545' ,"%Y%m%d%H%M").timetuple()))

	print "DONE READING SCHEDULE after %s, seconds"%(int(time.time()-st0))