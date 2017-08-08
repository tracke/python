#!/bin/python
# 
# 


# import required modules
from __future__ import print_function  #must be 1st
from numpy import *
import binascii as bin
import struct
import threading
import Queue
import sys, os
import serial
import time
from hub_table import *


#change hex to signed int
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
			   '03':'COMM_HUB_OPEN ',\
			   '06':"CONNECT ",\
			   '07':'ROOM_HUB_OPEN',\
			   '08':'ACK ',\
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
				'01':'SET TIME ',\
				'02':'SET CONFIG ',\
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

mesh_device = {'':" ",\
				'01': "Comm Hub",\
				'02': "Location Hub",\
				'03': "Hygiene Sensor",}
				 

	

## slices
#s_rssi=slice(0,3)
#s_len=slice(3,5)
#s_type=slice(5,7)
#s_sa=slice(7,19)
#s_da=slice(19,31)
#s_seq=slice(31,35)
#s_cmdevt=slice(35,39)




class packet(object):
	def __init__(self):
		self.sa = 0 #source addr
		self.da = 0 #dest addr
		self.rssi = -128 #rssi
		self.len = 0
		self.type = 0
		self.evt = 0 #mesh event
		self.payload=''
		pass


	def decode(self,data):		
		self.rssi = data[0:3]
		self.len = data[3:5]
		self.type = data[5:7]
		self.sa =rev_address(data[7:19])
		self.da =rev_address(data[19:31])
		self.seq = data[31:33]
		self.cmd_evt = data[33:35]
		if self.type == '03' or \
		   self.type == '07' or \
		   self.type == '09' or \
		   self.type == '0A' or \
		   self.type == '0C': 
			self.da='BROADCAST'
		elif self.type == '01':
			self.evt = data[33:35]
			self.payload = data[35:]
			self.process_payload1()
			#print(data)		
		elif self.type =="0B" or self.type == 11:
			self.evt = data[59:61]
			self.payload = bytes(data[61:])
			self.process_payload2((self.payload))
		else:
			if self.type == '0D' or self.type == '95':
				self.da = '0'	
			self.evt = '0'
		pass

	def process_payload1(self):
		#print("\r\nPAYLOAD 1:")
		if self.evt == '01': #set time
			time = rev_bytes(self.payload[0:8],8)
			print("\rSET TIME:",time,self.sa,"->",self.da)
			pass
		elif self.evt == '08': #ID CMD	
			print("\r\nIdentify CMD",self.sa,"->",self.da)
			pass
		elif self.evt == '5A':
			idx=self.payload[2:4]
			print("\r\n","USING 5A TO SET FIRMWARE ",self.sa,"->",self.da," idx",idx)
			#print(self.payload)			
		pass

	def process_payload2(self,payload):		
		if self.evt == '5A':  #SET FIRMWARE
			print("\r\nUSING 5A TO SET FIRMWARE\r\n",self.payload)
		elif self.evt == '47':   #RSSI REPORT
			s=struct.Struct('<12s8s2s')
			record_fmt=struct.Struct('12s2s2s2s8s8s')
			hub_source,time_stamp,hub_cnt =s.unpack(payload[0:22])
			sa = rev_address(hub_source)
			time=int(rev_bytes(time_stamp,8),16)
			record_len = 34
			#print("\r",time," ",rev_address(hub_source)," ",time_stamp," ",hub_cnt)
			for x in range(int(hub_cnt,16)):
				j=22+(x * record_len)
				a,b,c,d,e,f = record_fmt.unpack(payload[j:j+record_len])
				hwid = str(rev_address(a))
				devicetype = int(b)
				samples = int(c,16)
				rssi = hex2sint(d,8)
				mean = struct.unpack('<f',e.decode('hex'))[0]
				stddev = struct.unpack('<f',f.decode('hex'))[0]
				#print("HWID: ",hwid," Device Type:",devicetype,\
				#	"Max RSSI:",rssi,"#samples:",samples,\
				#	"MEAN:",mean,"STD DEV:",stddev)	
				rssi_table.buffer[0,x] = time,hwid,devicetype,samples,rssi,mean,stddev
				#print("rssi_array packed")
			#print(rssi_table.buffer)	
			rssi_table.append(sa)
			pass
		elif self.evt == '45': #DFU EVENT
			who=self.payload[1:7]
			devtype=self.payload[7:8]
			stat=self.payload[8:10]
			rev=self.payload[10:12]
			print("\r\nDFU EVENT for ",mesh_device.get(devtype)," ",who)
			pass
		elif self.evt ==  '46':  #IDHUB
			who = rev_address(self.payload[0:12])	
			devtype = self.payload[12:14]
			fware2 = self.payload[14:16]
			fware3 = int(self.payload[16:20],16)
			fware4 = int(self.payload[20:24],16)
			selftest = self.payload[24:26]
			battmv = self.payload[26:30]
			print("\r\nID HUB:",mesh_device.get(devtype)," ",who)
			print("FWARE2:",fware2,"\r\nFWARE3",fware3,"\r\nFWARE4",fware4)
			print("Self Test:",selftest,"\r\nBATT:",battmv,"mv")
			pass

			
	def print(self):
		print_buffer = "\r("+ str(int(time.time()))+ ") "+ str(self.rssi)+ " "
		if not (self.type == "01" or self.type== "0B"):
			print_buffer += (packet_type.get(self.type))
		if self.evt in mesh_event:	
			print_buffer += (mesh_event.get(self.evt) +" ")
		print_buffer +=	(self.sa + " -> " + self.da+"\r\n")
		sys.stdout.write(print_buffer)
		pass


# defined values
que_size=100

q=Queue.Queue(maxsize=que_size)
ser=serial.Serial()
frame=packet()
#HubTable=hub_table()
rssi_table=RSSI_TABLE(hub_cnt)


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
	print("\r\nStarting Input Thread....")
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
	print("\r\nStarting Process Thread")
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
			time.sleep(30)
			print("\r Buffer at ",(q.qsize()/que_size)*100,"%")
			#print("\r\nknown Hubs:",rssi_table.hubs)
			rssi_table.print_report(0)

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
	