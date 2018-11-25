import time
import socket
import sys
import os
import threading
import random
from myFunctionsLib import *

end_servers={}						#Contains the allias as key and the server address as value
files2download={}					#Contains the allias as key and the file link      as value
relay_nodes={}						#Contains the allias of the relay node as key and a Relay_node_object: node_allias,address,port

RTT_client_2_relay_nodes={}			#Contains the node's allias as key and the RTT for client->node
RTT_relay_nodes_2_end_servers={}	#Contains the node's allias as key and the RTT for node->end_server
RTT_SUM={}							#Contains the node's allias as key and the RTT for client->end_server

HOPS_client_2_relay_nodes={}		#Contains the node's allias as key and the HOPS for client->node
HOPS_relay_nodes_2_end_servers={}	#Contains the node's allias as key and the HOPS for node->end_server
HOPS_SUM={}							#Contains the node's allias as key and the HOPS for client->end_server

thread_list=[]
RECV_BUFFER_SIZE = 1024 

#Parse the parse_files

end_servers=parse_endservers("end_servers.txt")
files2download=parse_files2download("files2download.txt")
relay_nodes=parse_relay_nodes_file('relay_nodes.txt')

client_command=raw_input('Insert endserver\'s allias, count of tests and the kind of test\n')
allias_picked=client_command.split(" ",3)[0].strip()
if end_servers.has_key(allias_picked):
	server_picked=end_servers[allias_picked]
else: 
	sys.exit('There is no end_server with that allias.')
num_of_tests=client_command.split(" ",3)[1].strip()
choice=client_command.split(" ",3)[2].strip()
if choice.lower()!='latency' and choice.lower()!='hops' :
	sys.exit('Try again using a valid test')
print server_picked, num_of_tests, choice

#Get average RTT and number of HOPS directly to the end_server
direct_average_RTT=get_average_ping(server_picked,num_of_tests)
if direct_average_RTT!= '-1':	
	print "Average ping to "+allias_picked+" is: " + direct_average_RTT
else:
	print 'Could not ping to ',allias_picked,' server'

RTT_SUM['direct2server']=float(direct_average_RTT)
direct_HOPS=get_hops(server_picked)
print "Hops to", allias_picked, " is: ", direct_HOPS

HOPS_SUM['direct2server']=direct_HOPS
#THREAD FUNCTION
"""	
	Used for the first connection to a relay node.
	Sends a command to the relay node to get the average RTT for the number of
	ping tests the user enters and to perform a traceroute to find the number of hops
	from the relay node to the end_server the user requested. It receives all that
	from the client. Also in this method the average RTT
	and the number of HOPS to the relay node is calculated. 
	In the end saves the average RTTs hops results to each respective 
	dictionary using the node.allias as key value	
"""
def get_connections_analytics(node, server_picked,num_of_tests):
	threadLock.acquire(True)
	#CREATE TCP SOCKET
	sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#CONNECT TO RELAY NODE
	relay_server_address=(node.address, int(node.port))
	print 'Connecting to relay node:',node.allias,'\nIP: ',node.address,'\nPort: ',node.port
	sock.connect(relay_server_address)
	#Send signal to find avg RTT and hops to end_server
	try:
		average2relay_RTT=get_average_ping(node.address, num_of_tests)
		hops2relay=get_hops(node.address)
		RTT_client_2_relay_nodes[node.allias]=float(average2relay_RTT)
		HOPS_client_2_relay_nodes[node.allias]=int(hops2relay)
		print 'Average_RTT to',node.allias,'is: ',average2relay_RTT
		print 'HOPS to',node.allias,'is: ', hops2relay
		command='analytics'
		signal2relay=command + " " + server_picked + " " + num_of_tests
		sock.sendall(signal2relay)

		#Wait for response from relay
		data=sock.recv(RECV_BUFFER_SIZE)
		average_RTT=float(data.split(" ",1)[0].strip())
		hops=data.split(" ",1)[1]
		print 'average_RTT is: ', average_RTT
		print 'HOPS is: ', hops 
		#save rtt & hops to dictionaries
		RTT_relay_nodes_2_end_servers[node.allias]=float(average_RTT)
		HOPS_relay_nodes_2_end_servers[node.allias]=int(hops)

	finally:
		print "Closing socket"
		sock.close()

	#Release the lock before exiting thread
	threadLock.release()

"""
	In this function a signal is sent to the relay node that is proved to be faster
	to download the file from the end server and send it to back to the client.(i.e. This program)
"""
#THREAD FUNCTION
def download_image_from_relay(node,server_allias):
	threadLock.acquire()
	check_download=False
	file_link=files2download[server_allias]
	#CREATE TCP SOCKET
	sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	#CONNECT TO RELAY NODE
	relay_server_address=(node.address, int(node.port))
	print 'Connecting to relay node:',node.allias,'\nIP: ',node.address,'\nPort: ',node.port
	sock.connect(relay_server_address)
	try:
		#send command to download image
		command='download'
		signal2relay=command+" "+file_link+" "+node.allias
		sock.sendall(signal2relay)
		filename = 'client_downloads/'+ get_filename_from_link(files2download[allias_picked]) #set the file name to be saved
		print 'Filename is:' + filename
		#1 Receive size of the file
		filesize=sock.recv(RECV_BUFFER_SIZE)
		if filesize != 'download2relayError':
			print 'Filesize is:', filesize
			start_time = time.time()
			# 2 receive file
			try:
				with open(filename,'wb') as image_file:
					data=sock.recv(int(filesize))
					image_file.write(data)
				image_file.close()
			except IOError as e:
				print "I/O error({0}): {1}".format(e.errno, e.strerror)
	        
			end_time = time.time()
			#CATCH THE EXCEPTION
			download_time = end_time - start_time
			print 'Downloaded in:',download_time,' seconds.'
			#Check if file has downloaded and return true if yes or false if not.

			if os.path.isfile(filename):
				print 'File downloaded successfully in: ', download_time, ' seconds!'
				check_download= True
			else:
				print 'Error in downloading the file.'
				check_download= False
		else:
			print 'DOWNLOAD FAILED !! \nEncoutered an error while downloading file to the Relay Node.\n'

	except (RuntimeError, TypeError, NameError): 
		print 'Runtimme Error'
	except ValueError:
		print 'Invalid time value'
	except IOError as e:
	    print "I/O error({0}): {1}".format(e.errno, e.strerror)
	except socket.error as msg:
		print msg

	finally:
		print 'Closing socket'
		sock.close()

	threadLock.release()
	return check_download

	"""
	This function send an 'exit' command to every relay node
	to shut down.
	"""
#THREAD FUNCTION
def shutdown_relay_node(node):
	threadLock.acquire()
	sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	#CONNECT TO RELAY NODE
	relay_server_address=(node.address, int(node.port))
	print 'Connecting to relay node:',node.allias,'\nIP: ',node.address,'\nPort: ',node.port
	sock.connect(relay_server_address)
	#send command to download image
	sock.sendall('exit')
	sock.close()
	threadLock.release()


#List that contains the allias of a relay node
#with the minimum value of value of RTT or HOPS.
min_path_key_nodes=[] 

""" 
Insert the path or paths with the minimun hops in a list. If the lenght is >1 
try to find the best using another criterion
"""
def get_best_path_based_on_HOPS():
	del min_path_key_nodes[:] 	# Empty the list as a precaution.
	min_hops_count = 100 			# 30 hops is max, but just in case.
	for key in HOPS_SUM.keys():
		if HOPS_SUM[key]!=-1:
			if min_hops_count > HOPS_SUM[key]:
				min_hops_count = HOPS_SUM[key]
				del min_path_key_nodes[:]	# Deletes entire list.
				min_path_key_nodes.append(key)
			elif min_hops_count == HOPS_SUM[key]:
				min_path_key_nodes.append(key)

	if len(min_path_key_nodes) == 1:
		print 'Chose best path based on HOPS count'
		return min_path_key_nodes[0]
	elif len(min_path_key_nodes) > 1:
		del min_path_key_nodes[:]
		min_RTT=10000
		for key in RTT_SUM.keys():
			if RTT_SUM[key]!=-1:
				if min_RTT > RTT_SUM[key]:
					min_RTT = RTT_SUM[key]
					del min_path_key_nodes[:]
					min_path_key_nodes.append(key)
				elif min_RTT == RTT_SUM[key]:
					min_path_key_nodes.append(key)

		if len(min_path_key_nodes) == 1:
			print 'Chose best path base on RTT because we had multiple same HOPS count'
			return min_path_key_nodes[0]
		elif len(min_path_key_nodes) > 1:
			random_index = random.randint(0,len(min_path_key_nodes)-1)
			print 'Chose a path randomly because we had multiple same RTTs and HOPS count'
			return min_path_key_nodes[random_index]

def get_best_path_based_on_RTT():
	del min_path_key_nodes[:]		# Empty the list as a precaution.
	min_RTT = 10000					# A high random preset improbable value but just in case.
	for key in RTT_SUM.keys():
		if 	RTT_SUM[key]!=-1:
			if min_RTT > RTT_SUM[key]:
				min_RTT = RTT_SUM[key]
				del min_path_key_nodes[:]
				min_path_key_nodes.append(key)
			elif min_RTT == RTT_SUM[key]:
				min_path_key_nodes.append(key)

	if len(min_path_key_nodes) == 1:
		print 'Chose best path based on RTT'
		return min_path_key_nodes[0]
	elif len(min_path_key_nodes) > 1:
		del min_path_key_nodes[:] 	# Empty the list as a precaution.
		min_hops_count = 100 			# 30 hops is max, but just in case.
		for key in HOPS_SUM.keys():
			if HOPS_SUM[key]!=-1:
				if min_hops_count > HOPS_SUM[key]:
					min_hops_count = HOPS_SUM[key]
					del min_path_key_nodes[:]	# Deletes entire list.
					min_path_key_nodes.append(key)
				elif min_hops_count == HOPS_SUM[key]:
					min_path_key_nodes.append(key)

		if len(min_path_key_nodes) == 1:
			print 'Chose best path based on hops, BECAUSE we had multiple same average RTTs'
			return min_path_key_nodes[0]
		elif len(min_path_key_nodes) > 1:
			random_index = random.randint(0,len(min_path_key_nodes)-1)
			print 'Chose a path randomly because we had multiple same RTTs and HOPS count'
			return min_path_key_nodes[random_index]

def print_Choice_menu():
	print 'Pick one of the following. For example pick \"2\" or \" Full Mode\".\n'
	print '************************************** Menu *****************************************'
	print '*    1. Direct Mode (Only downloads through direct connection)                      *'
	print '*    2. Full Mode (Runs the analytics and chooses the best relay node or direct)    *'
	print '*    3. Exit (Exits the program)                                                    *'
	print '*************************************************************************************'
serversRunningFlag=False
while True:
	print_Choice_menu()
	menu_choice=raw_input('What would you like to do?\n')
	if menu_choice=='1' or menu_choice.lower()=='Direct Mode':	#lower() makes string lower case to ignore case sensitivity
		#CALL DIRECT DOWNLOAD
		fname=get_filename_from_link(files2download[allias_picked])
		print 'Filename is:' + fname
		start_time = time.time()
		if direct_download(files2download[allias_picked],allias_picked,fname)==True:
			end_time = time.time()
			download_time=end_time - start_time
			print 'Downloaded in:',download_time,' seconds.'
		else:
			print 'DIRECT DOWNLOAD ABORTED. FILE DOES NOT EXIST'
	elif menu_choice=='2' or menu_choice.lower()=='Full Mode':
		#CALL FULL MODE
		serversRunningFlag=True
		#create as many threads as the relay_nodes
		threadLock=threading.Lock()
		for node in relay_nodes.values():
			t=threading.Thread(target=get_connections_analytics,args=(node,server_picked, num_of_tests))
			t.setDaemon(True)
			thread_list.append(t)
			t.start()

		for thread_node in thread_list:
			thread_node.join()

		del thread_list[:]

		#calculate sum of hops and RTT for each relay node
		for key in relay_nodes.keys():
			RTT_SUM[key]=RTT_client_2_relay_nodes[key]+RTT_relay_nodes_2_end_servers[key]
			print 'RTT to relay-',key,' is:',RTT_client_2_relay_nodes[key]
			print 'RTT to server from relay-',key,' is:',RTT_relay_nodes_2_end_servers[key]
			print 'Total RTT Through Relay-',key,' is:',RTT_SUM[key]
			HOPS_SUM[key]=HOPS_client_2_relay_nodes[key]+HOPS_relay_nodes_2_end_servers[key]
			print 'HOPS to relay-',key,' is:',HOPS_client_2_relay_nodes[key]
			print 'HOPS to server from relay-',key,' is', HOPS_relay_nodes_2_end_servers[key]
			print 'Total HOPS through relay-',key,' is', HOPS_SUM[key]

		best_path=''
		if choice=='hops':
			best_path=get_best_path_based_on_HOPS()
		elif choice=='latency':
			best_path=get_best_path_based_on_RTT()


		if best_path == 'direct2server':
			fname=get_filename_from_link(files2download[allias_picked])
			print 'Filename is:' + fname
			start_time = time.time()
			if direct_download(files2download[allias_picked],allias_picked,fname)==True:
				end_time = time.time()
				download_time= end_time - start_time
				print 'Downloaded in:',download_time,' seconds.'
			else:
				print 'DIRECT DOWNLOAD ABORTED. FILE DOES NOT EXIST'
		elif best_path == '':
			print 'ERROR!!!! BEST PATH IS EMPTY.'
		else:
			threadLock=threading.Lock()
			t=threading.Thread(target=download_image_from_relay,args=(node,allias_picked))
			t.setDaemon(True)
			t.start()
			t.join()

	elif menu_choice=='3' or menu_choice.lower()=='Exit':
		
		if serversRunningFlag==True:
			#shutdown all servers
			#create as many threads as the relay_nodes
			threadLock=threading.Lock()
			for node in relay_nodes.values():
				t=threading.Thread(target=shutdown_relay_node,args=(node,))
				t.setDaemon(True)
				thread_list.append(t)
				t.start()

			for thread_node in thread_list:
				thread_node.join()

			del thread_list[:] 

			print 'Shutting down all relay nodes.'

		print 'Exiting Program...'
		break

	else :
		print 'Please choose one of the menu choices'
		continue
