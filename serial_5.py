#!/bin/python
# 
# 


# import required modules
from __future__ import print_function  #must be 1st
from numpy import *
import array
import binascii as bin
import struct
import threading
import Queue
import sys, os
import serial
import time



#change hex to sint
def hex2sint(x,bits=8):
	y=int(x,16)	
	h=1<<(bits-1)
	m=(1<<bits)-1
	return ((y+h)&m)-h


cursor = ['|','/','-','\\']

packet_type = {'0':'UNKNOWN',\
			    01 :'PAYLOAD',\
			    02 :'IDLE',\
			    03 :'COMM_HUB_OPEN',\
			    06 :"CONNECT",\
			    07 :'ROOM_HUB_OPEN',\
			     8 :'ACK',\
			     9 :'BCAST_WALL_SENSOR_ONLY',\
			    10 :'BCAST_ROOM_HUB_ONLY',\
			    11 :'PAYLOAD_2',\
			    12 :'RHUB_WALL_SENSOR_ONLY',\
			    13 :'RSSI_PING',\
			   '95':'BADGE_BCAST',\
				'00':'UNKNOWN',\
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

display = {'01':'yes',\
		   #'02':'',\
		   '95':'',\
		   '06':'',\
		   #'07':'',\
		   '08':'',\
		   '0B':'',\
		   '0D':''}			   

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
				'47':'RSSI REPORT',\
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

	

## slices
s_rssi=slice(0,3)
s_len=slice(3,5)
s_type=slice(5,7)
s_sa=slice(7,19)
s_da=slice(19,31)
s_seq=slice(31,35)
s_cmdevt=slice(35,39)







### RSSI TABLE ##############

record=dtype([('source',str_,12),\
			('time',int32),\
			('hwid',str_,12), \
			('type',uint8),\
			('samples',uint8),\
			('maxRSSI',int8),\
			('mean',float32),\
			('stddev',float32)])



class hub_table(object):
	def __init__(self):
		#rssi_array = array([arange(hub_cnt)],dtype=record)
		self.hubs=list()
		pass

	def if_exists(self,sa):
		if len(self.hubs):
			for x in range(len(self.hubs)):
				if self.hubs[x][0]==sa:
					return x
		else:
			return None		

	def add_hub(self,thisrecord):
		self.hubs.append(thisrecord)
		pass


	def update_hub(self,sa,thisrecord):
		if not self.if_exists(sa): 
			print("\r\nnew hub:",sa,"\r\n")
			self.add_hub(thisrecord)
			#self.create(sa)
			print("new table created")
		else:
			pass



	def lookup(self,sa):
		name='RSSI_'+sa
		try:
			name.shape
			return 1
		except:
			return 0
		pass
			
	def create(self,sa,hub_cnt=4):
		name='RSSI_'+sa
		name=array([arange(4)],dtype=record)	



	def update(self,hub_source,time_stamp,hub_record):
		thisrecord = list()
		sa = rev_address(hub_source)
		hwid = rev_address(hub_record[0])
		devicetype = int(hub_record[1],16)
		samples = int(hub_record[2],16)
		rssi = hex2sint(hub_record[3],8)
		mean = struct.unpack('<f',hub_record[4].decode('hex'))
		stddev = struct.unpack('<f',hub_record[5].decode('hex'))
		#if not self.lookup(sa):
		thisrecord=(hwid,devicetype,samples,rssi,mean,stddev)
		self.update_hub(sa,thisrecord)	


		print("HWID: ",hwid," Device Type:",devicetype,\
			"Max RSSI:",rssi,"#samples:",samples,\
			"MEAN:",mean,"STD DEV:",stddev)
		pass


		

		
	def print(self):

		pass

		


class packet(object):
	def __init__(self):
		self.sa = 0 #source addr
		self.da = 0 #dest addr
		self.rssi = -128 #rssi
		self.len = 0
		self.type = 0
		self.evt = 0 #mesh event
		self.payload=''
		

	def parse(self,data):
		print (data)


	def decode(self,data):		
		self.rssi = data[0:3]
		self.len = data[3:5]
		self.type = data[5:7]
		self.sa =rev_address(data[7:19])
		self.da =rev_address(data[19:31])
		self.seq = int(data[31:35],16)
		self.cmd_evt = data[35:39]

		if self.type == '03' or \
		   self.type == '07' or \
		   self.type == '09' or \
		   self.type == '0A' or \
		   self.type == '0C': 
			self.da='BROADCAST'
		elif self.type == '01':
			self.evt = data[35:39]
			self.payload = data[39:]
			self.process_payload1()
		
		elif self.type =="0B" or self.type == 11:
			self.evt = data[59:61]
			self.payload = bytes(data[61:])
			self.process_payload2((self.payload))
		else:
			if self.type == '0D' or self.type == '95':
				self.da = ''	
			self.evt = ''


	def process_payload1(self):
		print("\r\nPAYLOAD 1 -")
		print(self.type," ",self.evt," ",self.sa,"->",self.da)
		pass

	def process_payload2(self,payload):
		if self.evt == '47':   #RSSI REPORT
			s=struct.Struct('<12s8s2s')
			record_fmt=struct.Struct('12s2s2s2s8s8s')
			hub_source,time_stamp,hub_cnt =s.unpack(payload[0:22])
			hub_record = [[]for y in range(int(hub_cnt,16))]			
			record_len = 34
			#packed_data = bin.unhexlify(payload)
			print("\r",rev_address(hub_source)," ",time_stamp," ",hub_cnt)
			for x in range(int(hub_cnt,16)):
				j=22+(x * record_len)
				hub_record[:][x]+=record_fmt.unpack(payload[j:j+record_len])
				HubTable.update(hub_source,time_stamp,hub_record[:][x])				
				#print("Hub ",x,": ",hub_record[:][x])	

		

			
	def print(self):
		print_buffer = "\r"+ str(self.rssi) + " "
		if not (self.type == "01" or self.type== "0B"):
			print_buffer += (packet_type.get(self.type))
		print_buffer += (mesh_event.get(self.evt) +" ")
		print_buffer +=	(self.sa + " -> " + self.da+"\r\n")
		sys.stdout.write(print_buffer)


		pass

		





# defined values
que_size=100

q=Queue.Queue(maxsize=que_size)
ser=serial.Serial()
frame=packet()
HubTable=hub_table()



def rev_address(address):
	radd=''
	radd+=address[-2:]
	for i in range (1,6):
		radd+=address[-(i*2+2):-(i*2)]
	return radd


def rev_bytes(value,bytes):
	x=''
	x+=value[-2:]
	for i in range(bytes):
		x+=value[-(i*2+2):-(i*2)]
	return x




def open_port(ser,comm_port,baud):
	ser.port = comm_port
	ser.baudrate = baud #115200
	ser.bytesize = serial.EIGHTBITS #number of bits per bytes
	ser.parity = serial.PARITY_NONE #set parity check: no parity
	ser.stopbits = serial.STOPBITS_ONE #number of stop bits
	#ser.timeout = None          #block read
	#ser.timeout = search_timeout     #non-block read
	ser.timeout = 2              #timeout block read
	ser.xonxoff = False     #disable software flow control
	ser.rtscts = False     #disable hardware (RTS/CTS) flow control
	ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
	ser.writeTimeout = 2     #timeout for write
	try: 
		ser.open()
		ser.flushInput()
		ser.flushOutput()
		return(1)
	except Exception, e:
		print ("error opening serial port ", str(e))
		ser.close()
		return(0)
	pass


def get_packet(q,op):
	print("Starting Input Thread....")
	while op.isSet():
		try:
			data=ser.readline()
			if data.strip():
				if not q.full():
					packet=data.replace(" ","")
					q.put(bytes(packet[4:]))
				else:
					print("PACKET LOSS - queue size = ",q.qsize())    
		except Exception, e:	
			print("ERROR: ",str(e))
			op.clear()		


def process_packet(q,op):
	cur_idx=0
	print("Starting Process Thread")
	while op.isSet():
		try:
			while not q.empty():
				data=q.get()
				#print(data)
				#frame=data.replace(" ","")
				frame.decode(data)

				if frame.type in display:
					frame.print()
				else:
					print("\r",cursor[cur_idx],end='')
					cur_idx =(cur_idx+1)%len(cursor)

		except Exception, e:	
			print("ERROR: ",str(e))
			op.clear()		

			




def main(argv):
	if(len(argv)<3):   
		print ("usage: ",argv[0],"COMx baudrate")
		return    
	comm_port=argv[1]
	baud=argv[2]
	try:
		if not open_port(ser,comm_port,baud):
			return(0)
		op = threading.Event()	
		t1 = threading.Thread(name='input', target=get_packet,args=(q,op))
		t2 = threading.Thread(name='output', target=process_packet, args=(q,op))
		
		t1.setDaemon(True)
		t2.setDaemon(True)
		op.set() # start off good
		t1.start()
		t2.start()
		while op.isSet():
			time.sleep(10)
			print("\r Buffer at ",(q.qsize()/que_size)*100,"%")
	except Exception,e:	
		print("*ERROR -",str(e))
	finally:

		return		



if __name__ == "__main__":
	print("Starting",sys.argv[0],"...")
	main(sys.argv[0:])
	if(ser.isOpen()):
		ser.close() 
	print("fini")
	