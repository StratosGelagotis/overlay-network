import socket
import threading
import sys
import os
from myFunctionsLib import *

RECV_BUFFER_SIZE = 1024 
#CREATE TCP SOCKET
sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address=('192.168.1.66',1084)
print server_address
sock.bind(server_address)

while True:
	#Listen for incoming connections
	sock.listen(1)
	print "Waiting for connection"
	connection, client_address= sock.accept()


	try:

		print 'connection from ',client_address
		data= connection.recv(RECV_BUFFER_SIZE)
		command=data.split(" ",2)[0]
		
		if command=='analytics':
			server_picked=data.split(" ",2)[1]
			num_of_tests=data.split(" ",2)[2]
			print 'Server_picked is: ', server_picked
			print 'Num of tests is: ',num_of_tests
			#Calculate RTT & HOPS to the end_server
			average_ping=get_average_ping(server_picked, num_of_tests)
			hops=get_hops(server_picked)
			#Send data back to client
			signal2client=average_ping +" "+ str(hops)
			print 'avg RTT:',average_ping
			print 'HOPS:',hops
			connection.sendall(signal2client)

		elif command=='download':
			#TODO download image file
			file_link=data.split(" ",2)[1].strip()
			allias=data.split(" ",2)[2].strip()
			download=relay_download(file_link, allias) #returns true if everything is ok
			if download==True:
				print 'Sending image-file to client.'
				#send file to client
				filename='tmp_relay_downloads/tmp__'+allias+'__downloaded_file.png'
				filesize=os.path.getsize(filename)
				print 'Filesize is: ', filesize
				try:
					connection.sendall(str(filesize))
				except socket.error as msg:
					print msg
				try:
					with open(filename,'rb') as image_file:
						msg=image_file.read(int(filesize))
						connection.send(msg)
					image_file.close()
				except IOError as e:
					print "I/O error({0}): {1}".format(e.errno, e.strerror)

			else :
				print 'Error while downloading file from end_server to client.'
				connection.sendall('download2relayError')
		
		elif command=='exit':
			break
	    
	except socket.error as msg:
		print msg

	finally:
		connection.close()
