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


#event_function = {'01':evt_set_time, \
				  #'02':evt_set_config,\
				  #'04':evt_set_fware,\
				  #'06':evt_id_cmd,\
				  #'07':evt_start_mesh,\
				  #'08':evt_id_hub_08,\
				  #'09':evt_idhub_09,\
				  #'40':evt_old_dispense,\
				  #'42':evt_connect,\
				  #'44':evt_id,\
				  #'45':evt_dfu,\
				  #'46':evt_id_hub,\
				  #'47':evt_rssi_report,\
				  #'48':evt_none,\
				  #'49':evt_none,\
				  #'4A':'DISCONNECT ',\
				  #'4C':'CAP DATA ',\
				  #'4E':'HRTBT ',\
				  #'50':'OLD DISPENSE ',\
				  #'51':'VISIT ',\
				  #'52':'LQE ',\
				  #'53':'LQE 2 ',\
				  #'54':evt_none,\
				  #'55':evt_none,\
				  #'56':evt_none,\
				  #'57':evt_none,\
				  #'58':'VISIT ',\
				  #'59':'DISPENSE ',\
				  #'5A':'SET FWARE ',\
				  #'60':'CONNECT ',\
				  #'A5':'BADGE FWARE',}				

mesh_device = {'':" ",\
				'01': "Comm Hub",\
				'02': "Location Hub",\
				'03': "Hygiene Sensor", \
				'04': 'Badge'}
				 
file_save = False  # True saves data in .csv files
target_hwid = ''  # Hub hwid used for testing
	

#device Tx power - unknown,commhub,roomhub,wallsensor
tx_power={0:0,1:4,2:4,3:4,4:0}  


## slices
#s_rssi=slice(0,3)
#s_len=slice(3,5)
#s_type=slice(5,7)
#s_sa=slice(7,19)
#s_da=slice(19,31)
#s_seq=slice(31,35)
#s_cmdevt=slice(35,39)

def calc_distance(device,rssi,unit):
	REFERENCE_DISTANCE = 1.82
	P = tx_power.get(device)
	#P=0
	REFERENCE_PATH_LOSS = 49.31
	PATH_LOSS_EXP = 2.9
	PROXIMITY_PREFERENCE = 1   #.5
	dist=''
	if rssi > -128:
		dist = REFERENCE_DISTANCE * (10**(((P-rssi) - REFERENCE_PATH_LOSS) / (10 * PATH_LOSS_EXP)))
		
		if unit == 'FEET':
			dist *= 3.28084
	return dist





class packet(object):
	def __init__(self):
		self.sa = 0 #source addr
		self.da = 0 #dest addr
		self.rssi = -128 #rssi
		self.len = 0
		self.type = 0
		self.evt = 0 #mesh event
		self.payload=''
		self.data = ''
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
			print(data)		
		elif self.type =="0B" or self.type == 11:
			self.evt = data[59:61]
			self.payload = bytes(data[61:])
			self.process_payload2((self.payload))
		else:
			if self.type == '0D' or self.type == '95':
				self.da = '0'
				print("ping detected on Badge Freq. by",self.sa)	
			self.evt = '0'
		pass

	def process_payload1(self):
		if self.evt == '01': #set time
			time = rev_bytes(self.payload[0:8],8)
			print("\rSET TIME:",time,self.sa,"->",self.da)
			pass
		elif self.evt == '08': #ID CMD	
			print("\r\nIdentify CMD",self.sa,"->",self.da)
			pass
		elif self.evt == '42': #Connect CMD	
			print("\r\nConnect",self.da)
			pass	
		elif self.evt == '4A': #Disconnect CMD	
			print("\r\nDisonnect",self.sa,"->",self.da)
			pass		
		elif self.evt == '5A':
			idx=self.payload[2:4]
			print("\r\n","USING 5A TO SET FIRMWARE ",self.sa,"->",self.da," idx",idx)
			#print(self.payload)
		else:
			print("\r\nPAYLOAD 1:")
			print("\r\n ",self.sa,"->",self.da,self.payload)	
		pass

	def process_payload2(self,payload):

		if not self.sa == target_hwid:
			#print(self.sa,"->")
			return
		self.data =''		
		if self.evt == '5A':  #SET FIRMWARE
			print("\r\nUSING 5A TO SET FIRMWARE\r\n",self.payload)
			pass

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
				dist = calc_distance(devicetype,mean,'FEET')

				#rssi_table.buffer[0,x] = sa,time,hwid,devicetype,samples,rssi,mean,stddev
				if devicetype==3:
					self.data+=("\r\n"+sa+" reports Dispenser at Node"+str(x)+":"+hwid+" "+str(rssi)+"dbm "+"at  "+str(dist)+" feet'\r\n")
			#rssi_table.append(sa)
			pass

		#elif self.evt == '45': #DFU EVENT
			#who=self.payload[0:12]
			#devtype=self.payload[12:14]
			#stat=self.payload[14:10]
			#rev=self.payload[10:12]
			#print("\r\nDFU EVENT for ",mesh_device.get(devtype)," ",who)
			#pass
		#elif self.evt ==  '46':  #IDHUB
			#who = rev_address(self.payload[0:12])	
			#devtype = self.payload[12:14]
			#fware2 = int(self.payload[14:16],16)
			#fware3 = int(self.payload[16:20],16)
			#fware4 = int(self.payload[20:24],16)
			#selftest = self.payload[24:26]
			#battmv = self.payload[26:30]
			#print("\r\nID HUB:",mesh_device.get(devtype)," ",who)
			#print("FWARE2:",fware2,"\r\nFWARE3",fware3,"\r\nFWARE4",fware4)
			#print("Self Test:",selftest,"\r\nBATT:",battmv,"mv")
			#pass

		elif self.evt == '58' :  # Ext Visit
			s=struct.Struct('12s4s4s4s4s8s2s')
			badge,hub_fware,batt_mv,\
			badge_fware,hash_cfg, time_stamp,cnt = s.unpack(payload[0:38])
			badge_fware = rev_bytes(badge_fware,4)
			cnt=int(cnt,16)
			badge=rev_address(badge)
			#print("Hub:",self.sa,"rev",int(rev_bytes(hub_fware,4),16))
			#print("Badge: ",rev_address(badge)," fware:",int(badge_fware,16), \
			#	  "  Batt(mv):",int(rev_bytes(batt_mv,4),16), "Samples:",cnt,end='')
			sum=0
			count=0
			sec=0
			avg=0
			values=''
			#print("\rHub ",self.sa," Reporting Badge ",badge," at")
			for x in range(0,cnt*2,2):
				i=x+38
				j=x+40
				k=int(payload[i:j],16)
				rssi=k & 63
				accel = (k & 192) >> 4
				if(rssi <= 62):
					rssi = -(rssi+19)
					sum += rssi	
					count += 1
				elif rssi > 62:
					rssi = -128
				sec +=1	
				#dist1 = calc_distance(4,rssi,'FEET')
				#print(int(time_stamp,16) + sec,"-> ",rssi,"dbm at",dist1,"feet")	
				#print(rssi,", ",end='')

			avg=sum/count			
			dist = calc_distance(4,avg,'FEET')
			print("\r Hub ",self.sa," Reports Badge ",badge," with RSSI of ",avg,"dbm ", \
				   "{:.2f}".format(dist)," feet away")

			#print(" Avg RSSI: ",avg)

			pass

			#print( "\r\n!!VISIT!!")
			#pass			

		elif self.evt == '59':
			print( "\r\n!!DISPENSE!!")
			pass
		elif self.evt == '60':
			print("Connected")				

		#else:
			#print("\r\nPAYLOAD 2:")
			#print("evt:",self.evt," -> ",end='')
			#print(self.payload)	
			
	def print(self):
		#print_buffer = "\r("+ str(int(time.time()))+ ") "+ str(self.rssi)+ " "
		#if not (self.type == "01" or self.type== "0B"):
			#print_buffer += (packet_type.get(self.type))
		#if self.evt in mesh_event:	
			#print_buffer += (mesh_event.get(self.evt) +" ")
		#print_buffer +=	(self.sa + " -> " + self.da+"\r\n")
		#sys.stdout.write(print_buffer)
		sys.stdout.write(self.data)
		self.data=''
		pass


# defined values
que_size=100

q=Queue.Queue(maxsize=que_size)
ser=serial.Serial()
frame=packet()
#HubTable=hub_table()
rssi_table=RSSI_TABLE(hub_cnt,file_save)


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
				frame.decode(data)
				if frame.type in display:
					frame.print()
					pass
				else:
					print("\r",cursor[cur_idx],"\r",end='')
					cur_idx =(cur_idx+1)%len(cursor)
		except Exception, e:	
			print("ERROR: ",str(e))
			op.clear()		

			

def main(argv):
	global target_hwid
	if(len(argv)<5):   
		print ("usage: ",argv[0],"COMx baudrate Freq Hub HWID")
		return    
	comm_port=argv[1]
	baud=argv[2]
	freq=int(argv[3])
	if not freq < 79 and freq > 73:
		freq=78
	if not argv[4] == '0':
		target_hwid = argv[4]
	else:
		target_hwid = '5D358CDAED0D'

	print("using data from Hub ",target_hwid)		

	try:
		if not open_port(ser,comm_port,baud):
			return(0)
		freq_cmd = "F"+ argv[3]	
		line1="setting frequency to 24."+ str(argv[3])+"MHz"
		print(line1 )
		ser.write(freq_cmd)	
		

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
			print(" looking for data from ",target_hwid)
			#print("\r Buffer at ",(q.qsize()/que_size)*100,"%")
			#print("\r\nknown Hubs:",rssi_table.hubs)
			#rssi_table.print_report(0)
			#rssi.table.find_hwid('0')
			#print(rssi_table.get_hubs())
			#rssi_table.print_table()


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
	