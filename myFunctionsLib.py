import subprocess
import urllib2
import os.path
import threading
import requests
class Relay_node_object:

	def __init__(self,allias,address,port):
		self.allias=allias
		self.address=address
		self.port=port
	def __str__(self):
		ret=self.allias+" "+self.address+" "+ self.port
		return ret
	#CAUTION repr MIGHT CAUSE PROBLEM 
	def __repr__(self):
		ret=self.allias+" "+self.address+" "+ self.port
		return ret

def get_average_ping(end_server,num_of_tests):
	last_line=int(num_of_tests)+5
	prelast_line=int(num_of_tests)+4
	average=''
	try:
		for line in subprocess.check_output(['ping', '-c', num_of_tests , end_server]).splitlines()[prelast_line:last_line]:
			#print 'Line is:\n',line
			average=line.rpartition('=')[-1].split("/",4)[1]
			#print 'New average print:', average
	except subprocess.CalledProcessError :
		print 'Server not responding. \nServer Made in Japan'
		return '-1'
	#average= [line.rpartition('=')[-1].split("/",4)[1] for line in subprocess.check_output(['ping', '-c', num_of_tests , end_server]).splitlines()[prelast_line:last_line]]
	return average

def get_hops(end_server): #, num_of_tests):
	#run traceroute in background
	commandOutput=subprocess.check_output(['traceroute', end_server]).splitlines()
	outputLen=len(commandOutput)
	#print 'First Traceroute line:',commandOutput[0]
	end_servers_ip=commandOutput[0].split(' ',10)[3].split(',')[0]
	print 'End server\'s IP is:',end_servers_ip
	
	#print 'Last traceroute line:',commandOutput[outputLen-1],'--'
	last_ip_hoped=commandOutput[outputLen-1].split(' ',9)[4].strip()
	print "Last IP hopped is:",last_ip_hoped	# if the  last line is *** then the ip is returned as a '*'
	if(end_servers_ip == last_ip_hoped):
		print 'HOPS SUCCESS'
		hops=outputLen-1 #my modem is not included in the hops
		return hops
	else:
		print 'HOPS FAILED'
		hops=-1
		return hops

def direct_download(file_link,allias,fname):
	file_link=file_link.strip()
	print 'File link is:',file_link
	#httpResponse=httpResponseFileExists(file_link)
	#if httpResponse==True:
	if httpResponseFileExists(file_link)==True:
		file = urllib2.urlopen(file_link)
		file_name='direct_downloads/'+ fname
		print 'Direct Download from ',allias,' server '
		print 'Filename is:'+fname
		print 'File is downloading...'
		with open(file_name,'wb') as output:
	  		output.write(file.read())
		
		if os.path.isfile(file_name):
			print 'File downloaded successfully.'
			return True
		else:
			print 'Error in downloading the file.'
			return False
	else:
		print 'FILE LINK IS BROKEN.\nFILE DIRECT DOWNLOAD ABORTED'
		return False

def relay_download(file_link,allias):
	print 'File link is:',file_link
	if httpResponseFileExists(file_link)==True:
		file = urllib2.urlopen(file_link)
		file_name='tmp_relay_downloads/tmp__'+allias +'__downloaded_file.png'
		print 'Relay Download from ',allias,' server '
		print 'File is downloading...'
		with open(file_name,'wb') as output:
	  		output.write(file.read())
		
		if os.path.isfile(file_name):
			print 'File downloaded successfully.'
			return True
		else:
			print 'Error in downloading the file.'
			return False
	else:
		print 'FILE LINK IS BROKEN.\nFILE DOWNLOAD TO RELAY ABORTED'
		return False
		
def parse_relay_nodes_file(filename):
	rn_nodes={}
	with open(filename,"r") as rn_file:
		for line in rn_file:
			allias=line.split(",",3)[0].strip()
			address=line.split(",",3)[1].strip()
			port=line.split(",",3)[2].strip()
			#print allias, address, port
			node=Relay_node_object(allias,address,port)
			rn_nodes[allias]=node

	return rn_nodes

#http://www.mit.edu/~gil/images/mit_logo.gif
def get_filename_from_link(filelink):
	strlist=filelink.split("/")
	filename=strlist[len(strlist)-1]
	return filename


def parse_files2download(filename):
	files2download={}
	end_servers_aliasses=['google','mit','grnet','bbc-uk','ucla','caid','japan-go','anu','inspire','youtube']
	with open(filename,"r") as files2download_file:
		i=0	
		for line in files2download_file:
			files2download[end_servers_aliasses[i]]=line
			i+=1

	return files2download
	
def parse_endservers(filename):
	end_servers={}
	with open(filename, "r") as end_servers_file:
		for line in end_servers_file:	
			end_servers[line.split(" ",1)[1].strip()]=line.split(" ",1)[0].strip(",")
	return end_servers

"""
This function checks if a link for a file is correct.
If the HTTP response from the server is different than 200
then the file-link is broken and the file doesn't exist
"""
def httpResponseFileExists(filelink):
	try:
		r = requests.head(filelink)
		httpstatus=r.status_code
		print 'HTTP RESPONSE IS: ',httpstatus
		if httpstatus==200:
			return True
		else:
			return False
		# prints the int of the status code. Find more at httpstatusrappers.com :)
	except requests.ConnectionError:
		print("failed to connect")

