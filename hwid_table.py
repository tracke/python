#!/bin/python
# 
# HWID Table implementation
# The device table will contain data for all of the hubs that are issuing 
# RSSI_REPORT packets. When a packet is received the rssi array will be populated with
# the data from the report.
# The source address of the hwid of the hub issuing the report
# aka sa will be compared to entries in the hubs list. 
# If the sa is found it's element number will be used as an index into the rssi table
# to locate the data record from that sa. The contents of the rssi array will be compared
# to the existing data(?) or will overwrite the existing data
#
# If the source address is not found it will be appended to the hubs list and the rssi array
# will be vertically stacked with the rssi table (RSSI_TABLE=vstack((RSSI_TABLE,rssi_array))
# placing the new data at the next index of the array
# 
#DEVICE_TABLE([[(0, '0', 0, 0, 0, 0.0, 0.0), (1, '1', 1, 1, 1, 1.0, 1.0), <----- records from 
#             (2, '2', 2, 2, 2, 2.0, 2.0), (3, '3', 3, 3, 3, 3.0, 3.0)],<----- hwid at hubs[0]
#            [(0, '0', 0, 0, 0, 0.0, 0.0), (1, '1', 1, 1, 1, 1.0, 1.0), <----- records from
#             (2, '2', 2, 2, 2, 2.0, 2.0), (3, '3', 3, 3, 3, 3.0, 3.0)]]<----- hwid at hubs[1]
#
# Changes:
#	2.0  	08/11/2017 added Source Address hwid to beginning of the RSSI array & table.
#			Create composite log file and write all rssi reports to it

# import required modules
from __future__ import print_function  #must be 1st
#from numpy import *
import binascii as bin
import struct
import sys, os
import serial
import time
import csv



# Current Mesh Devices 
Mesh_device = {'':" ",\
				'01': "Comm Hub",\
				'02': "Location Hub",\
				'03': "Hygiene Sensor",\
				'04': "Badge    ",\
				'05': "Asset Tag",}
				 

#create a list for indexing the hubs issueing reports
hubs=list()

# the number of adjacent hubs captured
hub_cnt = 4


# create a record type for a device:
#   <hwid><RSSI><rssi adj><current fware><battery mv><accel reading>
#   <new fware><image index><'extra'><dfu error>

#===================================================================================================
# device_record=([('hwid',str_,12),\
# 			('device_type',int16), \
# 			('rssi',str_,3),\
# 			('rssi_adj',int16),\
# 			('curr_fware',int16), \
# 			('battmv',int16),\
# 			('accel',str_,2),\
# 			('sent_fware',int16),\
# 			('dfu_idx',int16),\
# 			('extra',int16),\
# 			('dfu_err',int16),\
# 			('recent',int16), \
# 			('cov',int16)])
# 		
#===================================================================================================


class HWID_TABLE(object):
	def __init__(self,file_save=True):
		self.file_save =  file_save
		self.table_lock = 0
		self.buffer = []
		self.table1=[['hwid',\
			'device_type', \
			'rssi',\
			'rssi_adj',\
			'curr_fware', \
			'battmv',\
			'accel',\
			'sent_fware',\
			'dfu_idx',\
			'extra',\
			'dfu_err',\
			'recent', \
			'cov']]
		self.table = [[] for x in xrange(len(self.table1))]
		self.hubs=list('0')
		self.hubcnt=len(self.hubs)
		self.logfile1=("ASSET_TAG_DFU"+time.strftime("%m_%d_%Y")+".csv")
		with open(self.logfile1, 'a+')as fp1:
				csv_writer=csv.writer(fp1)
				csv_writer.writerow(self.table1[0])


# simple lock to control access to table 
	def lock_table(self):
		while self.table_lock == 1: { }
		self.table_lock = 1
		return
	
	def release_table(self):
		self.table_lock = 0
		return
## 	
		
		
	def append(self,sa):
#		print("\rlooking for..",sa,end="")
		while self.table_lock:{}
		self.lock_table()
		try:
			num=int(sa,16)
			if sa in self.hubs:
				idx=self.hubs.index(sa)
				if (self.table[idx][1] != self.buffer[1]) or \
					(self.table[idx][4] != self.buffer[4]):
					print("device type for ",self.table[idx][0],"has changed")
					print("from",self.table[idx][1],"to",self.buffer[1])
					if self.file_save == True:
						self.buffer[10] = 'YES'
						with open(self.logfile1, 'a+') as fp:
							csv_writer=csv.writer(fp)
							csv_writer.writerow(self.buffer)
				self.table[idx]=self.buffer			
			else:	
				self.hubs.append(sa)
				self.table.append(self.buffer)
				print("\r\n",Mesh_device.get(self.buffer[1]),sa,"added to  list at idx",self.hubs.index(sa))
				if self.file_save == True:
					with open(self.logfile1, 'a+') as fp:
						csv_writer=csv.writer(fp)
						csv_writer.writerow(self.buffer)
	
		except Exception, e:
			print("\r",sa,"error checking Table")	
			
		self.release_table()
		self.clear_buffer()	
		pass

	
	def get_size(self):
		return len(self.hubs)
	
	
	def update(self):
		recs = len(self.hubs)
		idx = 1
		self.lock_table()
#		print(recs-1,"recs")
		while (idx < recs):
#		for idx in range(1,recs-1):
			self.table[idx]=list(self.table[idx])
			if self.table[idx][11] >= 2:  # old data - remove
#				print(self.table[idx])
				this_hwid=self.table[idx][0]
				if this_hwid in self.hubs:
					self.hubs.remove(this_hwid)
					recs -= 1
#					print("removing ",this_hwid,"at idx",idx)
					self.table.pop(idx)
#			print(idx," ",recs-1)
			idx +=1	
#		print("release")	
		self.release_table()	
		pass
		
		
	def clear_recent(self):
		recs=len(self.hubs)
		self.lock_table()		
		for idx in range(1,recs):
			self.table[idx]=list(self.table[idx])
			self.table[idx][11] += 1			
			pass
		self.release_table()
		

	def get_recent_cnt(self):
		recs=len(self.hubs)
		cnt = 0
		self.table_lock
		for idx in range(1,recs):
			if self.table[idx][11] < 2:
				cnt += 1
		self.release_table()		
		return cnt
			
	
	def print_table(self):
		recs=len(self.hubs)
		cnt = self.get_recent_cnt()
		num=1
#		print("\r\nShowing ",cnt,"entries")
		for idx in range(1,recs):
			self.lock_table()
			hwid=self.table[idx][0]
			device = Mesh_device.get(self.table[idx][1])
#			if self.table[idx][1]=="04":
#				device = "BADGE"
#			elif self.table[idx][1] == "05":
#				device = "TAG"
			rssi = self.table[idx][2]	
			curr_fware = self.table[idx][4]
			battmv = self.table[idx][5]
			accel = self.table[idx][6]
			new_fware = self.table[idx][7]
			dfu_idx = self.table[idx][8]
			ext = self.table[idx][9]
			recent = self.table[idx][11]
			self.release_table()	
			if recent < 2:
				print("\r\n",idx,") ",rssi,device,hwid,"accel:",accel,ext,battmv,"mv","Rev",curr_fware,end="") #,"with Rev",curr_fware,end="")
				num +=1
				if (new_fware > 0) and (new_fware <1000):
					print (" working on index",dfu_idx,"of Rev",new_fware,end="")
				if recent == 1:
					print("*",end="")	
			time.sleep(0.1)	
	
			
			
				
	
	
	
	
	def get_cnts(self):
		cnts=[0,0]
		recs=len(self.hubs)
		for idx in range(1,recs):
			self.lock_table()
			if self.table[idx][11] < 2:
				if self.table[idx][1] == "04":
#					print("HWID is a BADGE")
					cnts[0]+=1
				elif self.table[idx][1] == "05":
#					print("HWID is a TAG")
					cnts[1]+=1
			self.release_table()	
		return cnts		
			
	
	
	
	def get_cnts_old(self):
		cnts=[0,0]
		recs=len(self.hubs)
#		print("Searching ",recs,"records...")
		for idx in range(1,recs):
			if(self.table[idx][0][1] == 4 ):
#				print("HWID is a BADGE")
				cnts[0]+=1
			elif(self.table[idx][0][1] == 5):
#				print("HWID is a TAG")
				cnts[1]+=1
#		print("cnts:",cnts)		
		return cnts			
				
	
	def get_array(self,sa):
		try:
			idx=self.hubs.index(sa)
			return self.table[sa]
		except:
			print("error accessing record")	
			return 0

	def get_record(self,sa,entry):
		try:
			idx=self.hubs.index(sa)
			return self.table[sa,entry]
		except:
			print("error accessing record")	
			return 0		

	def get_hubs(self):
		return self.hubs

	def print_record(self,sa):
		if sa in self.hubs:
			idx=self.hubs.index(sa)
			#print(5*' ',"Time",12*' ',"HWID","   ","Type")
			for i in range(self.hubcnt):
					print(self.table[idx,i])
		else:
			print("Report error:",sa,"not found in hub list")
			print(self.hubs)

	def print_report(self,sa):
		if sa != 0:
			print("RSSI Table Report for Hub",sa)
			self.print_record(sa)
		else:
			print("RSSI Table Report for all Hubs\r\n")
			for i in range(len(self.hubs)):
				print("\r\n",self.hubs[i],":")
				self.print_record(self.hubs[i])
		pass
		
	
				

	def clear_buffer(self):
		self.buffer=""
#		self.buffer[0,] = ""


