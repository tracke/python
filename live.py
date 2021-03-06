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
from radar_table import *
from hub_radar import *
from utils import *

ut =  Util()
ut.debug = False


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

def calc_distance(rssi,unit):
	REFERENCE_DISTANCE = 1.82
	REFERENCE_PATH_LOSS = 49.31
	PATH_LOSS_EXP = 2.9
	PROXIMITY_PREFERENCE = 1.5
	dist=''
	if rssi > -128:
		dist= REFERENCE_DISTANCE * (10**(((-rssi) - REFERENCE_PATH_LOSS) / (10 * PATH_LOSS_EXP)))
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
		self.data=''
		pass


	def decode(self,data):
		self.data=''		
		self.rssi = data[0:3]
		self.len = data[3:5]
		self.type = data[5:7]
		self.sa =rev_address(data[7:19])
		self.da =rev_address(data[19:31])
		self.seq = data[31:33]
		self.cmd_evt = data[33:35]
		if self.type =="0B" or self.type == 11:
			self.evt = data[59:61]
			self.payload = bytes(data[61:])
			self.process_payload2((self.payload))
		else:
			if self.type == '0D' or self.type == '95':
				self.da = '0'	
			self.evt = '0'
		pass

	
	def process_payload2(self,payload):		
		if self.evt == '5A':  #SET FIRMWARE
			#print("\r\nUSING 5A TO SET FIRMWARE\r\n",self.payload)
			pass
		elif self.evt == '47':   #RSSI REPORT
			s=struct.Struct('<12s8s2s')
			record_fmt=struct.Struct('12s2s2s2s8s8s')
			hub_source,time_stamp,hub_cnt =s.unpack(payload[0:22])
			sa = rev_address(hub_source)
			time=int(rev_bytes(time_stamp,8),16)
			record_len = 34
			self.data =''
			for x in range(int(hub_cnt,16)):
				j=22+(x * record_len)
				a,b,c,d,e,f = record_fmt.unpack(payload[j:j+record_len])
				hwid = str(rev_address(a))
				devicetype = int(b)
				samples = int(c,16)
				rssi = hex2sint(d,8)				
				mean = struct.unpack('<f',e.decode('hex'))[0]				
				stddev = struct.unpack('<f',f.decode('hex'))[0]
				norm_mean = mean + 128
				dist = calc_distance(mean,'FEET')
				if hwid == '000000000000':
					hwid = 'RESET'
				graph_data.buffer[0,x] = sa,time,hwid,devicetype,samples,dist,norm_mean,stddev
				if devicetype==3:
					self.data+=("Dispenser at Node"+str(x)+":"+hwid+" "+str(rssi)+"dbm "+"at  "+str(dist)+" meters\r\n")
			graph_data.add_record(sa)
			#print(":",self.data)
			#print("record added")
			pass
		elif self.evt == '58':
			print( "\r\n!!VISIT!!")
			pass



			
	def print(self):
		print_buffer = "\r\n("+ str(int(time.time()))+ ") "+ str(self.rssi)+ " "
		if not (self.type == "01" or self.type== "0B"):
			print_buffer += (packet_type.get(self.type))
		if self.evt in mesh_event:	
			print_buffer += (mesh_event.get(self.evt) +" ")
		print_buffer +=	(self.sa + " -> " + self.da+"\r\n")
		pass


# defined values
que_size=100

q=Queue.Queue(maxsize=que_size)
ser=serial.Serial()
frame=packet()
#HubTable=hub_table()
rssi_table=RSSI_TABLE(hub_cnt)
graph_data = RadarTable(hub_cnt)
disp=HubRadar()

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
					#dprint("\r",cursor[cur_idx],"\r",end='')
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
	freq=int(argv[3])
	if not freq < 79 and freq > 73:
		freq=78


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
			time.sleep(5)
	
			#print("\r Buffer at ",(q.qsize()/que_size)*100,"%")
			#print("\r\nknown Hubs:",rssi_table.hubs)
			#rssi_table.print_report(0)
			#rssi.table.find_hwid('0')
			#node_num=len(graph_data.nodes)
			node_num=10  #max nodes
			hub_num=len(graph_data.hubs)
			#print(hub_num,"Hub(s) reporting ", node_num,"Nodes:")
			#print("Nodes Reported:",graph_data.nodes)
			#print(graph_data.table[0])
			#for i in range(len(graph_data.table[1])):
			#	print("\r\n",graph_data.table[1][i])

			#print("Update Graphs")
			if hub_num >=4:
				disp.nrows=hub_num / 3
				disp.ncols=3
				if disp.nrows*disp.ncols < hub_num:
					disp.nrows+=1
				disp.nodes=node_num
				disp.hubs=hub_num
				disp(graph_data.table)
				pass	
			#print("\r\nTable Data:",graph_data.table,"\r\n")
			if hub_num:				
				#dprint("Finding nodes")
				for n in range(len(graph_data.nodes)):
					this_node=graph_data.nodes[n]
					#dprint ("Finding Node:",n,":",this_node)					
					this_node_data = graph_data.find_node(this_node)
					if this_node_data:
						print ("\r\nNode ",n,"-",this_node,":")
						#print(this_node_data)
						for x in range(len(this_node_data)):
							hwid = this_node_data[x][0]
							dist = calc_distance(this_node_data[x][1],'FEET')
							print((x+1),") is ","{:.2f}".format(dist)," feet from hub ",hwid )




	except Exception,e:	
		print("*ERROR -",str(e))
	finally:

		return		



if __name__ == "__main__":
	if len(sys.argv) < 4:
		print("Usage:",sys.argv[0],"<sp>COMx<sp>Baud<sp>Frequency channel")
		print("Example:",sys.argv[0]," COM3 115200 78")
	# if arguments are there we can start...	
	print("Starting",sys.argv[0],"...")
	main(sys.argv[0:])
	if(ser.isOpen()):
		ser.close() 
	print("fini")
	