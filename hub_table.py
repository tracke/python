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
#   <timestamp><hwid><device type><# of samples>
#   <max rssi><mean of rssi samples><std dev of samples>

hub_record=dtype([('time',int32),\
			('hwid',str_,12), \
			('type',uint8),\
			('samples',uint8),\
			('maxRSSI',int8),\
			('mean',float32),\
			('stddev',float32)])


# create a record entry for the rssi array. 
# this will be used as a buffer to hold data from the RSSI_REPORT packet
#rssi_array = array([arange(hub_cnt)],dtype=hub_record)

# create the inital record of the RSSI_TABLE array
#RSSI_TABLE = array([arange(hub_cnt)],dtype=hub_record)


# Define the methods for operating on the array
#

class RSSI_TABLE(object):
	def __init__(self,hub_cnt):
		self.buffer = array([arange(hub_cnt)],dtype=hub_record)
		self.table = array([arange(hub_cnt)],dtype=hub_record)
		self.hubs=list()
		self.hubcnt=hub_cnt
		self.logfile=("log"+time.strftime("%d_%m_%Y")+".csv")
		pass

	def append(self,sa):
		#print("looking for ",sa)
		if sa in self.hubs:
			idx=self.hubs.index(sa)
			#print ("\r\nFound",sa,"at idx",idx)
			self.table[idx,]=self.buffer
		else:	
			self.hubs.append(sa)
			self.table=vstack((self.table,self.buffer))
			print("\r\nHub ",sa,"added to hubs list at idx",self.hubs.index(sa))
			#if not self.table[self.hubs.index(sa),0:] == self.buffer:	
				#print("**ERROR ADDING DATA**")
			#print("known hubs:",self.hubs)
		# Write as a CSV file with headers on first line
		with open(self.logfile, 'a+') as fp:
			for idx in range(len(self.hubs)):
				fp.write(self.hubs[idx] + '\r\n')
				fp.write(','.join(self.table.dtype.names) + '\n')
				for i in range(self.hubcnt):
					fp.write(str(self.table[idx,i])+'\r\n')


			#savetxt(fp, self.table, '%s', ',')
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
				print("\r\n[",self.hubs[i],"]:")
				self.print_record(self.hubs[i])

	def clear_buffer(self):
		self.buffer[:] = 0


