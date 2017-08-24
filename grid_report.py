#!\bin\python









from __future__ import print_function  #must be 1st
#from __future__ import divide
#from numpy import *
import binascii as bin
import struct
import threading
import Queue
import sys, os
import serial
import time
import csv
from mpl_toolkits.mplot3d import axes3d
import matplotlib.pyplot as plt
import numpy as np



# file format:
# time_stamp, Node ID,Device Type,# of samples,Max RSSI,Mean RSSI,STD DEV 
fields = {}
time_events = []
entries = []
headers=[]
nodes = {}
rssi ={}
hwids = []
event_nodes={'START':'','MOVE 1':'','MOVE 2':'','MOVE 3':''}
X_Data = list()


class map_data(object):
	def __ini__(self):
		self.rpt_hub={}
		self.src_hub={}
		self.data_array 






def cnt_node(hwid,idx):
	r=fields['mean'][idx]
	if hwid in nodes:
		num = nodes.get(hwid)
		r1 = rssi.get(hwid)
		num += 1
		nodes[hwid] = num
		if r > r1:
			rssi[hwid] = r
		pass
	else:
		nodes[hwid] = 1
		rssi[hwid] = r
	pass
	


def set_node(event):
	hwids=['','','','']
	#print(event," : ",nodes)
	for y in range(0,4):
		v = 0
		vals={}
		for x in nodes:
			v1=nodes.get(x)
			#print(x," : ",v1)			
			if v1 > v:
				v=v1				
				hwids[y] = x	
		nodes[hwids[y]]=0
	event_nodes[event]=hwids
	pass



def set_event_node(event):
	hwids=[['']for x in range(4)]
	means=[['']for x in range(4)]
	for y in range(0,4):
		v=0
		for x in nodes:
			v1=nodes.get(x)
			r1=rssi.get(x)
			if v1 > v:
				v=v1				
				hwids[y] = (x,r1)	
		nodes[hwids[y][0]]=0
	event_nodes[event]=hwids
	pass

def get_times(f):
	global start_time
	global stop_time 
	start_time = 9999999999
	stop_time = 0
	with open(f,'rt') as fp:
		data = csv.reader(fp)
		for row in data:
			if any(row):
				if row[0] == 'source':
					pass					
				else:
					if int(row[1]) < int(start_time):
						start_time = row[1]
					if row[1] > stop_time:
						stop_time = row[1]	
	#print('Start:',start_time,'End:',stop_time )						

def map_hwids(f):
	recs = 0
	zero = 0
	with open(f,'rt')as fp:
		try:
			data = csv.reader(fp)
			for row in data:
				if any(row):
					if row[0] == 'source':
						headers.append(row)					
					else:
						if not row[2]=='000000000000':
							recs +=1						
							if row[2] in hwids:
								pass
								#print(row[2],"already exists")						
							else:							
								#print('adding ',row[2])
								hwids.append(row[2])
						else:
							zero +=1
		except Exception,e:
			print("*ERROR -",str(e))
	get_times(f)
	x_scale = (int(stop_time) - int(start_time))/60

	visual=[[''for x in range(len(hwids))] for y in range(len(hwids))]
	grid_data=[[int(start_time)+(t*60),[[-128 for x in range(len(hwids))] for y in range(len(hwids))]] for t in range(x_scale+1)]
	#grid_data=[[[''for x in range(len(hwids))] for y in range(len(hwids))] for t in range(x_scale+1)]
	
	print(len(grid_data))
	for i in range(x_scale+1):
		#print (grid_data[i])
		pass

	print("working with entries from ",start_time," to ",stop_time,"in steps of",x_scale)
	for x in hwids:				
		with open(f,'rt')as fp:
			data=csv.reader(fp)
			#print(hwids)
			print("finding records for ",x,' idx',hwids.index(x))
			k=0
			t=int(start_time)
			t_next = t+60		
			for row in data:
				if any(row):
					if row[0] == 'source':
						print('Headers!')
						pass
					else:
						if row[2] == x: 
							tim = int(row[1])
							this_t = (tim-t)/60
							#if tim > t_next:
								#t = t_next
								#t_next = t+60
								#print(this_t,hwids.index(x),hwids.index(row[0]))
								#pass
							#elif tim >= t:
								#this_t = (tim-t)/60
							
							#print(row[0],"",row[1]," ",row[2]," ",row[5])
							#visual[:] = grid_data1[this_t-1][1]
							#print(this_t,hwids.index(x),[hwids.index(row[0])])

							#visual[hwids.index(x)][hwids.index(row[0])]=row[5]


							#print(int(row[1]),visual)
							#grid_data[this_t][hwids.index(x)][hwids.index(row[0])]=row[5]
							grid_data[this_t][1][hwids.index(row[0])][hwids.index(x)]=row[5]
							#print(this_t," (",tim,") ",row[0],"->",grid_data[this_t])
							#grid_data.append((this_t,visual))
							#print(grid_data1[this_t])
						##print(row[1]," ",t," ",t_next)
						#if int(row[1]) >= int(t_next):
							##print("this record is for next time frame")
							#t = t_next
							#t_next=t+60
							#grid_data.append((t,visual))
							#if t > int(stop_time):
								#break
						#elif row[1] >= t: 
							##print ("record within timeframe")
							#if row[2] == x:
								#visual[hwids.index(x)][hwids.index(row[0])]=row[5]
								##print(t,";",row[0],":",visual)



						else: 
						#print('not this record')
							pass	

			else:
				#print('no data !')			
				pass

	
	for i in range(len(hwids)):
		print(10*" ",hwids[i],10*" ",end='')
	print("\r\n")	


	for i in range(len(grid_data)):
		#print(grid_data[i])
		pass

	for this_t in range(len(grid_data)/4):
		#for i in range(len(hwids)):
		i=1
		for j in range(len(hwids)):
			X_Data.append((i,j,grid_data[this_t][1][i][j]))

	#print(X_Data)		
	fig=plt.figure()
	ax = fig.add_subplot(111,projection = '3d')
	#X, Y, Z = get_test_data()
	for i in range(len(X_Data)):
		X,Y,Z = X_Data[i]
		print("X:",X,"Y",Y,"Z:",Z)
		c=X+Y
		ax.scatter(float(X), float(Y),float(Z))
	plt.show()

							
									
		



def get_event(time_stamp):
	#print("get event for ",time_stamp,end='') 
	for x in range(0,len(time_events)-1):
		if time_stamp >= int(time_events[x][0]) and time_stamp < int(time_events[x+1][0]):
	#		print(time_events[x][1])
			return time_events[x][1]



def read_file(f):
	print('reading parameter file')
	with open('time_parameters.csv', 'rt') as p:
		events = csv.reader(p)
		i=0
		for row in events:
			#print(i," ",row)
			time_events.append([row[0],row[1]])			
			i+=1		
	#print (time_events)

	print("reading csv file")
	with open(f, 'rt') as fp:
		try:			
			data = csv.reader(fp)
			sa = data.next()
			headers = data.next()

			#print("Headers:",headers)
			for h in headers:
				fields[h] = []
			for row in data:
				if not row[2] == '': # ignore blank rows and rows with only the hwid
					if not row[0] == 'time': # ignore header rows 
						for h, v in zip(headers, row):
							fields[h].append(v)
			#print(fields)	
			#print ("Data Loaded...")
			#Set up cols for Change & Event
			headers.append('Change')
			headers.append('Event')
			fields['Change'] = []
			fields['Event'] = []
			#print(headers)

			rows = len(fields['time'])
			cols = len(fields)

			for x in range(rows):
				fields["Change"].append('')
				fields['Event'].append('')
			change =''
			for x in range(rows):
				if x >3:
					xp=x-4 
					if not fields['time'] ==' ' :
						tim = int(fields['time'][x])
						fields['Event'][x] = get_event(tim)										
						if fields['hwid'][x] == fields['hwid'][xp]:
							fields['Change'][x] = '*' 
						else:
							fields['Change'][x] = 'Node Changed'						
					else:
						fields['time'][x] = '<blank>'


			for e in range(len(time_events)):
				for x in range(rows):
					if fields['Event'][x] == time_events[e][1]:
						cnt_node(fields['hwid'][x],x)				
				#set_node(time_events[e][1])
				set_event_node(time_events[e][1])

			for x in event_nodes:
				print(x," : ",event_nodes[x])


				
			report_file = (sa[0] + "_log.csv")

			with open(report_file, 'w+')as fp:
				print ("Writing Report file ",report_file)
				fp.write("Report file for Node "+ sa[0] +"\r\n")
				fp.write("4 Nodes with strongest RSSIs per Test Step:\r\n")
				for x in event_nodes:
					fp.write(x + "," + str(event_nodes[x])+"\r")	
				fp.write("\r\n Raw Data:\r\n")	
				fp.write(",".join(headers)+"\r\n")
				for x in range(0,rows):
					for y in range(0,cols):
						h = headers[y]
						fp.write(fields[h][x])
					fp.write("\r")
		except Exception,e:
			print("*ERROR -",str(e))					
		



def write_params():
	f = "time_parameters.csv"
	tim_input =" "
	with open(f, 'a+')as fp:
		try:
			while tim_input != "":
				tim_input = raw_input("enter time stamp:")
				event = raw_input("enter the event:")
				entry = ','.join((tim_input,event))
				fp.write(entry + "\n")
				print ("wrote",tim_input,event,"to file",f)
		except Exception,e:	
			print("*ERROR -",str(e))



def main(argv):
	if argv[1] == "W" or argv[1] == "w":
		write_params()
	elif argv[1] == "R" or argv[1] == "r":
		read_file(argv[2]) 	
	elif argv[1] == 'M' or argv[1] =='m':
		map_hwids(argv[2])
	else:

		# do operations on composite file	
		print('Not implemented.\r\n Choose "W" or "R"')
	
	


if __name__ == "__main__":
	print("Starting",sys.argv[0],"...")
	main(sys.argv[0:])
	print("fini")


