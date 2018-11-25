Python Version: 2.7.6
Directories "client_downloads","direct_downloads","tmp_relay_downloads"
are necessary to Run the project.

Possibly the ip adressess in the relay_nodes.txt file need to be changed to run in a
different computer.
ifconfig to find your local ip.

relay_node.py, relay_node1.py, relay_node2.py, relay_node3.py are IDENTICAL except
they include different ports. It's possible  that the ip addressess need to be 
changed to run in a different environment

myFunctionsLib.py is a python file which contains functions that are called by the
client and all the relay_nodes. This file is absolutely necessary to run the project.

Linux operating system is required to run the project.

Open 5 terminals. 1 for the client and 4 for the relay_nodes
1)Run one relay_node in each of the 4 terminals like below:
For Terminal 1) python relay_node.py
For Terminal 2) python relay_node1.py
For Terminal 3) python relay_node2.py
For Terminal 4) python relay_node3.py
Now we wait for the client to communicate

Run the client in the remaining 5th terminal like below:
python client.py 
The client.py reads the end_servers.txt, relay_nodes.txt and the files2download.txt automatically.

In the command line insert: the allias, the number of ping tests and the criterion 
like below:
google 10 hops

then you can choose between the following 3 options:
1) Direct Mode, if you want to download a file directly from the end_server
2) Full Mode, if you want to connect through the relay nodes and download through the
fastest connection(including directly to the server)
3) Exit, to exit the program.

NOTE: To run the 1st option you don't need to start any relay_node script.

After the 1st and 2nd options you will be returned to this menu to choose what you want
to do again.

