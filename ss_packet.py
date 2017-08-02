# serial try
#
#
import struct
import threading
import Queue
import os
import serial
from bitstring import ConstBitStream



packet_type = {'0':'UNKNOWN',\
			   '01':'PAYLOAD',\
			   '02':'IDLE',\
			   '03':'COMM_HUB_OPEN',\
			   '06':"CONNECT",\
			   '07':'ROOM_HUB_OPEN',\
			   '08':'ACK',\
			   '09':'BCAST_WALL_SENSOR_ONLY',\
			   '0A':'BCAST_ROOM_HUB_ONLY',\
			   '0B':'PAYLOAD_2',\
			   '0C':'RHUB_WALL_SENSOR_ONLY',\
			   '0D':'RSSI_PING',\
			   '95':'BADGE_BCAST'}

mesh_event = {'':' ',\
				'01':'SET TIME',\
				'02':'SET CONFIG',\
				'04':'OLD SET FWARE ',\
				'06':'ID CMD ',\
				'07':'START MESH ',\
				'08':'IDHUB CMD 08 ',\
				'09':'IDHUB CMS 09 ',\
				'40':'OLD DISP ',\
				'42':'CONNECT ',\
				'44':'ID ',\
				'45':'DFU ',\
				'46':'IDHUB ',\
				'47':'RSSI ',\
				'48':'N/A ',\
				'49':'N/A ',\
				'4A':'DISCONNECT ',\
				'4C':'CAP DATA ',\
				'4E':'HRTBT ',\
				'50':'OLD DISPENSE ',\
				'51':'VISIT ',\
				'52':'LQE ',\
				'53':'LQE 2 ',\
				'54':'N/A ',\
				'55':'N/A ',\
				'56':'N/A ',\
				'57':'N/A ',\
				'58':'VISIT ',\
				'59':'DISPENSE ',\
				'5A':'SET FWARE ',\
				'60':'CONNECT ',\
				'A5':'BADGE FWARE',}

display = {'01':'yes',\
			'02':'',\
		   '95':'',\
		   '06':'',\
		   '07':'',\
		   '08':'',\
		   '0B':'',\
		   '0D':''}

class packet(object):
	def __init__(self):
		self.sa = 0 #source addr
		self.da = 0 #dest addr
		self.rssi = -128 #rssi
		self.len = 0
		self.type = 0
		self.evt = 0 #mesh event

	def parse(self,data):
		print data


	def decode(self,data):
		address_len=6
		i=0
		self.tmp = ''
		data.pos+=48
		self.rssi = '-'
		self.sa = ''
		self.da=''
		self.len = ''
		self.type = ''
		self.evt = ''
		self.rssi += chr(data.read('uint:8'))
		self.rssi += chr(data.read('uint:8'))
		data.pos += 32
		self.len += chr(data.read('uint:8'))
		self.len += chr(data.read('uint:8'))
		data.pos +=8
		self.type += chr(data.read('uint:8'))
		self.type += chr(data.read('uint:8'))
		data.pos+=8
		while i<address_len:
			self.sa += chr(data.read('uint:8'))
			self.sa += chr(data.read('uint:8'))
			data.pos+=8
			i+=1
			
		i=0
		while i<address_len:
			self.da += chr(data.read('uint:8'))
			self.da += chr(data.read('uint:8'))
			data.pos+=8
			i+=1	

		if self.type in ('01','0B'):
			data.pos +=24
			self.evt += chr(data.read('uint:8'))
			self.evt += chr(data.read('uint:8'))	
		return


#######################################################
# OFFSETS
#######################################################

TIMESTAMP = 0
HUB_NO = 4
HUB_1_HWID = 6
HUB_1_

		

    



