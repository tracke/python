#!/bin/python
# 
# 


# import required modules
from __future__ import print_function  #must be 1st
import struct
import threading
import Queue
import sys, os
import serial
import time


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
		print (data)


	def decode(self,data):		
		self.rssi = str(data[4:7])
		self.sa=(data[11:23])
		self.da=data[23:35]
		if self.da == '000000000000':
			self.da='BROADCAST'
		self.len = int(data[8:9],16)
		self.type = data[9:11]
		if self.type =="0B" or self.type == 11:
			self.evt = data[63:65]
		else:	
			self.evt = ''
			
	def print(self):
		pass

		


# defined values
que_size=100

q=Queue.Queue(maxsize=que_size)
ser=serial.Serial()
frame=packet()

def rev_address(address):

	for i in range (0,len(address)):
		address[i]=address[len(address)-(i+1):-i]




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


def get_packet(q):
	print("Start Input Thread....")
	while True:
		data=ser.readline()
		if data.strip():
			if q.qsize() <= que_size:
				q.put(data)	    
			else:
				print("PACKET LOSS - queue size = ",q.qsize())    
		pass

def print_packet(q):
	print("Start Print Thread")
	while True:
		while not q.empty():
			data=q.get()
			#frame=data.replace(" ","")
			frame.decode(data.replace(" ",""))
			print(frame.rssi,frame.type,packet_type.get(frame.type),\
				  " ",mesh_event.get(frame.evt), \
				 # " ",frame.evt,\
				  frame.sa,"-->",frame.da)
				  #rev_address(frame.sa))
			#print(data)



def main(argv):
	if(len(argv)<3):   
		print ("usage: ",argv[0],"COMx baudrate")
		return    
	comm_port=argv[1]
	baud=argv[2]
	if not open_port(ser,comm_port,baud):
		return(0)
	t1 = threading.Thread(name='input', target=get_packet,args=(q,))
	t2 = threading.Thread(name='output', target=print_packet, args=(q,))
	t1.setDaemon(True)
	t2.setDaemon(True)
	t1.start()
	t2.start()
	while True:
		time.sleep(10)
		print("Buffer at ",(q.qsize()/que_size)*100,"%")
  



if __name__ == "__main__":
	print("Starting",sys.argv[0],"...")
	main(sys.argv[0:])
	if(ser.isOpen()):
		ser.close() 
	print("fini")
	