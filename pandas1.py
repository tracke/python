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
						if not row[2]=='000000000001': #'1' should be '0'
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
	idx=hwids.index(row)+1
	return idx


def make_hub_dataframes():
	for j in range(len(hwids)):
		#make a dataframe for each reporting hub
		pass
	pass



def main(argv):

	# NOTE: pandas will autodetec the size of the terminal and will
	#		display the data in chunks accordingly.
	#		Set the options for a wide screen to display all of the columns
	pd.set_option('display.height', 1000)
	pd.set_option('display.max_rows', 500)
	pd.set_option('display.max_columns', 500)
	pd.set_option('display.width', 1000)
	
	map_hwids('Composite_Log18_08_2017.csv')
	
	df2 = pd.read_csv('Composite_Log18_08_2017.csv',skip_blank_lines=True)
	print(df2.head())

	make_hub_dataframes()
	

	df2['src_idx'] = df2['source'].apply(get_hwid_idx,axis=1)
	df2['node_idx'] = df2['hwid'].apply(get_hwid_idx,axis=1)
	
	df3 = pd.pivot_table(df2,values='mean',index=['time','source','src_idx'], columns=['node_idx'])
	
	#df3 = df3.drop('000000000000', axis=1)
	df3 = df3.drop(7, axis=1)
	df3 = df3.fillna(-128)  # Hubs not recorded can be assigned rssi of -128
	
	#df3.to_csv('Pivot_Data_11_08_2017.csv')
	
	print(df3)
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





if __name__ == "__main__":
	print("Starting",sys.argv[0],"...")
	main(sys.argv[0:])
	print("fini")
