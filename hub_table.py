#!/bin/python
# 
# RSSI Table implementation
# The rssi table will contain data for all of the hubs that are issuing 
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
#RSSI_TABLE([[(0, '0', 0, 0, 0, 0.0, 0.0), (1, '1', 1, 1, 1, 1.0, 1.0), <----- records from 
#             (2, '2', 2, 2, 2, 2.0, 2.0), (3, '3', 3, 3, 3, 3.0, 3.0)],<----- hwid at hubs[0]
#            [(0, '0', 0, 0, 0, 0.0, 0.0), (1, '1', 1, 1, 1, 1.0, 1.0), <----- records from
#             (2, '2', 2, 2, 2, 2.0, 2.0), (3, '3', 3, 3, 3, 3.0, 3.0)]]<----- hwid at hubs[1]
#
# Changes:
#	2.0  	08/11/2017 added Source Address hwid to beginning of the RSSI array & table.
#			Create composite log file and write all rssi reports to it

# import required modules
from __future__ import print_function  #must be 1st
from numpy import *
import binascii as bin
import struct
import sys, os
import serial
import time
import csv


#create a list for indexing the hubs issueing reports
hubs=list()

# the number of adjacent hubs captured
hub_cnt = 4


# create a record type for a recorded hub:
#   <source><timestamp><hwid><device type><# of samples>
#   <max rssi><mean of rssi samples><std dev of samples>

hub_record=dtype([('source',str_,12),\
			('time',int32),\
			('hwid',str_,12), \
			('type',uint8),\
			('samples',uint8),\
			('maxRSSI',int8),\
			('mean',float32),\
			('stddev',float32)])


#

class RSSI_TABLE(object):
	def __init__(self,hub_cnt,file_save=True):
		self.file_save =  file_save
		self.buffer = array([arange(hub_cnt)],dtype=hub_record)
		self.table = array([arange(hub_cnt)],dtype=hub_record)
		self.hubs=list()
		self.hubcnt=hub_cnt
		self.logfile=("log"+time.strftime("%d_%m_%Y")+".csv")
		self.logfile1=("Composite_Log"+time.strftime("%d_%m_%Y")+".csv")
		with open(self.logfile1, 'a+')as fp1:
				csv_writer=csv.writer(fp1)
				csv_writer.writerow(self.table.dtype.names)
		pass

	def append(self,sa):
		print("\rlooking for ",sa)
		if sa in self.hubs:
			idx=self.hubs.index(sa)
			print ("\r\nFound",sa,"at idx",idx)
			self.table[idx,]=self.buffer
			if self.file_save == True:
				with open(sa + self.logfile, 'a+') as fp:
					csv_writer=csv.writer(fp)
					csv_writer.writerows(self.buffer[0])
				with open(self.logfile1, 'a+') as fp1:
					csv_writer=csv.writer(fp1)
					csv_writer.writerows(self.buffer[0])

		else:	
			self.hubs.append(sa)
			self.table=vstack((self.table,self.buffer))
			print("\r\nHub ",sa,"added to hubs list at idx",self.hubs.index(sa))
			ssa = []
			ssa.append(sa) # place sa as element so we can print w/csv_writer
			if self.file_save == True:
				with open(sa + self.logfile, 'a+') as fp:
					csv_writer=csv.writer(fp)
					csv_writer.writerow(ssa)
					csv_writer.writerows(self.buffer[0])
				with open(self.logfile1, 'a+') as fp1:
					csv_writer=csv.writer(fp1)
					csv_writer.writerows(self.buffer[0])				
		self.clear_buffer()	
		pass

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
		
	def print_table(self):
		print(self.table)
		pass
				

	def clear_buffer(self):
		self.buffer[:] = 0


