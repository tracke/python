#!/bin/python
# originally written for python 2.x
# 
from __future__ import print_function  #must be 1st
import os, sys
import csv
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm



hwids = []
headers=[]
dfs=dict()

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
						if not row[2]== '0': #'1' should be '0'
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
	print('HWIDS:',hwids)
	pass		

def get_hwid_idx(row,axis):
	#print(row)
	if not row =='0':
		idx=hwids.index(row)+1
		return idx
	pass

def calc_distance(row,axis):
	REFERENCE_DISTANCE = 1.82
	REFERENCE_PATH_LOSS = 49.31
	PATH_LOSS_EXP = 2.9
	PROXIMITY_PREFERENCE = 1.5
	dist=''
	if row > -128:
		dist= REFERENCE_DISTANCE * (10**(((-row) - REFERENCE_PATH_LOSS) / (10 * PATH_LOSS_EXP)))
	return dist


def make_hub_dataframes(df):
	# make separate datarames for each reporting hub
	# and create a pivot table, filling the empty values 
	# with -128(dbm)
	for i in range(len(hwids)):
		this_df = (hwids[i] + "_df")
		this_df = df[df.source == hwids[i]]
		this_df = pd.pivot_table(this_df,values=['mean','distance'],index=['time','source','src_idx'], columns=['node_idx'])
		#this_df = this_df.fillna(-128)
		print("\r\n",hwids[i],":",this_df.head())
		this_df.to_csv((hwids[i] +"_log.csv"))
		dfs[i] = this_df
		pass
	pass



def make_hub_radarframes(df):
	for i in range(len(hwids)):
		this_rf = (hwids[i] + "_rf")
		this_rf = df[df.source == hwids[i]]
		print(this_rf.head())
	pass




def graph_rssi(df,hub):
	X=df.index.get_level_values('time')
	#print("X:",X)
	Y=df.columns.get_level_values('node_idx')
	#print("Y:",Y)
	X,Y = np.meshgrid(X,Y)
	#z=df[['mean']
	Z=np.transpose(df.values) #[['mean']])
	fig=plt.figure()
	#ax = fig.add_subplot(111,projection = '3d')
	title = 'Hub '+ str(hub+1) + ' reporting:'+ hwids[hub] 

	ax = fig.add_subplot(1,1,1,projection = '3d')
	ax.set_ylabel('Nodes')
	ax.set_title(title)
	ax.set_zlabel('dbm')
	ax.set_ylim(1,6)
	ax.set_zlim(-128,-30)
	ax.set_yticklabels((hwids[:])) #0], hwids[1], hwids[0], hwids[0], hwids[0]))
	#ax2 = fig.add_subplot(1,2,2,projection = '3d')
	#ax.plot_surface(X,Y,Z,rstride=1, cstride=1,cmap=cm.coolwarm,linewidth=0,antialiased=False)
	#ax.scatter(X,Y,Z)
	#ax.plot_wireframe(X,Y,Z)
	ax.plot_surface(X,Y,Z,rstride = 1,cstride=1,cmap='cool',shade=True)
	#plt.show()
	


def main(argv):
	f=argv[1]

	# NOTE: pandas will autodetec the size of the terminal and will
	#		display the data in chunks accordingly.
	#		Set the options for a wide screen to display all of the columns
	pd.set_option('display.height', 1000)
	pd.set_option('display.max_rows', 500)
	pd.set_option('display.max_columns', 500)
	pd.set_option('display.width', 1000)
	
	#map_hwids('Composite_Log11_08_2017.csv')
	map_hwids(f)
	#df2 = pd.read_csv('Composite_Log11_08_2017.csv',skip_blank_lines=True)
	df2 = pd.read_csv(f,skip_blank_lines=True)


	df2['src_idx'] = df2['source'].apply(get_hwid_idx,axis=1)
	df2['node_idx'] = df2['hwid'].apply(get_hwid_idx,axis=1)
	df2['distance'] = df2['mean'].apply(calc_distance,axis=1)
	
	#print(df2.head())

	#make_hub_dataframes(df2)

	make_hub_radarframes(df2)


	df3 = pd.pivot_table(df2,values='mean',index=['time','source','src_idx'], columns=['node_idx'])

	
	#df3 = df3.drop('000000000000', axis=1)
	#df3 = df3.drop(7, axis=1)
	#df3 = df3.fillna(-128)  # Hubs not recorded can be assigned rssi of -128
	#print(df3.head())

	for i in range(len(hwids)):
		if not hwids[i]=='0':
			graph_rssi(dfs[i],i) 


	plt.show()


def nothing():
	
	#df3.to_csv('Pivot_Data_11_08_2017.csv')
	
	#print(df3)
	X=df3.columns
	#print("X:",X)
	Y=df3.index.get_level_values('src_idx')
	#print("Y:",Y)
	X,Y = np.meshgrid(X,Y)
	Z=df3.values
	#
	fig=plt.figure()
	#ax = fig.add_subplot(111,projection = '3d')
	ax1 = fig.add_subplot(1,2,1,projection = '3d')
	#ax2 = fig.add_subplot(1,2,2,projection = '3d')
	#ax.plot_surface(X,Y,Z,rstride=1, cstride=1,cmap=cm.coolwarm,linewidth=0,antialiased=False)
	ax1.scatter(X,Y,Z)
	#print(df3.index)
	#ig.scatter(df3['src_idx'],df3['node_idx'],df['Close'])
	plt.show()
	pass




if __name__ == "__main__":
	print("Starting",sys.argv[0],"...")
	if len(sys.argv) < 2:
		print("You must specify a file to open")
	else:
		print(sys.argv)		
		main(sys.argv[0:])
	print("fini")
