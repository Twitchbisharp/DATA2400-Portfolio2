import argparse
import sys
import ipaddress
from socket import *
import _thread as thread
from threading import Thread

'''
    #Utility functions: 1) to create a packet of 1472 bytes with header (12 bytes) (sequence number, acknowledgement number,
    #flags and receiver window) and applicaton data (1460 bytes), and 2) to parse
    # the extracted header from the application data. 
'''

from struct import *

# I integer (unsigned long) = 4bytes and H (unsigned short integer 2 bytes)
# see the struct official page for more info

header_format = '!IIHH'             #("(4), (4), (2), (2)")

#print the header size: total = 12
print (f'size of the header = {calcsize(header_format)}')


def create_packet(seq, ack, flags, win, data):
    #creates a packet with header information and application data
    #the input arguments are sequence number, acknowledgment number
    #flags (we only use 4 bits),  receiver window and application data 
    #struct.pack returns a bytes object containing the header values
    #packed according to the header_format !IIHH
    header = pack (header_format, seq, ack, flags, win)

    #once we create a header, we add the application data to create a packet
    #of 1472 bytes
    packet = header + data
    print (f'packet containing header + data of size {len(packet)}') #just to show the length of the packet
    return packet


def parse_header(header):
    #taks a header of 12 bytes as an argument,
    #unpacks the value based on the specified header_format
    #and return a tuple with the values
    header_from_msg = unpack(header_format, header)
    #parse_flags(flags)
    return header_from_msg
    

def parse_flags(flags):
    #we only parse the first 3 fields because we're not 
    #using rst in our implementation
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin

#now let's create a packet with sequence number 1
print ('\n\ncreating a packet')

data = b'0' * 1460
print (f'app data for size ={len(data)}')

sequence_number = 1
acknowledgment_number = 0
window = 0 # window value should always be sent from the receiver-side
flags = 0 # we are not going to set any flags when we send a data packet

#msg now holds a packet, including our custom header and data
msg = create_packet(sequence_number, acknowledgment_number, flags, window, data)

#now let's look at the header
#we already know that the header is in the first 12 bytes

header_from_msg = msg[:12]
print(len(header_from_msg))

#now we get the header from the parse_header function
#which unpacks the values based on the header_format that 
#we specified
seq, ack, flags, win = parse_header (header_from_msg)
print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')

#let's extract the data_from_msg that holds
#the application data of 1460 bytes
data_from_msg = msg[12:]
print (len(data_from_msg))


#let's mimic an acknowledgment packet from the receiver-end
#now let's create a packet with acknowledgement number 1
#an acknowledgment packet from the receiver should have no data
#only the header with acknowledgment number, ack_flag=1, win=6400
data = b'' 
print('\n\nCreating an acknowledgment packet:')
print (f'this is an empty packet with no data ={len(data)}')

sequence_number = 0
acknowledgment_number = 1   #an ack for the last sequnce
window = 0 # window value should always be sent from the receiver-side

# let's look at the last 4 bits:  S A F R
# 0 0 0 0 represents no flags
# 0 1 0 0  ack flag set, and the decimal equivalent is 4
flags = 4 

msg = create_packet(sequence_number, acknowledgment_number, flags, window, data)
print (f'this is an acknowledgment packet of header size={len(msg)}')

#let's parse the header
seq, ack, flags, win = parse_header (msg) #it's an ack message with only the header
print(f'seq={seq}, ack={ack}, flags={flags}, receiver-window={win}')

#now let's parse the flag field
syn, ack, fin = parse_flags(flags)
print (f'syn_flag = {syn}, fin_flag={fin}, and ack_flag={ack}')



"""------------------------------------------------------------------------------------------------------------------------------------------------------------"""

def check_port(val):                
    try:
        int(val)                    #Tests if input can be an integer
    except:
        raise argparse.ArgumentTypeError("The port number", val, "is not an integer", type(val))    #Error-message if not integer

    val = int(val)                  #Make the input an integer
    if val >= 1024 and val <= 65535:#Checks if the integer is between 1024 and 65535
        return val                  #Ok to return
    else:
        raise argparse.ArgumentTypeError("The port number must be between 1024 and 65535") #Error-message if not between [1024, 65535]

def check_ip(val):                          
    try:
        val = ipaddress.ip_address(val)     #Checks with the ipaddress import if it's a valid IP
    except:
        raise argparse.ArgumentTypeError("IP-address syntax wrong") #Error-message if IP-syntax is wrong
    return val                              #If the test was OK, return the value

def serverSyncer(connectionSocket, recvWord, sendWord):        
    while True:     #infinite loop untill 'break'
        connectionSocket.send(sendWord.encode())        #send the sendWord to client
        message = connectionSocket.recv(99999).decode() #recieve everything that the client sendt
        if recvWord in message:                         #if the message contains the wanted recvWord
            print(recvWord)                             #print the wanted recvWord
            break                                       #exit the loop
        else:
            continue


def clientSyncer(client_sd, recvWord, sendWord):           
    while True:     #infinite loop
        message = client_sd.recv(2048).decode() #takes in a message from server if there are any
        if recvWord in message:                 #if message contains recvWord
            client_sd.send(sendWord.encode())   #send message back to server that client got it
            print(recvWord)                     #print wanted word
            break                               #exit loop
                                

def server(arguments): #initial server function
    serverSocket = socket(AF_INET, SOCK_DGRAM) #make a server socket
    try:
        serverSocket.bind((str(arguments.bind), arguments.port))    #Try to bind to a specific port and ip
    except:
        print("Bind failed - Wait and try again, or check if the IP-address is supported") #if the bind failed, report and error-message
        sys.exit()                                                                         #and exit the program
    
    serverSocket.listen(10)                                 #listen to any clients that wants to connect
    print("\nID\t\t\tInterval\tTransfer\tBandwidth\n")      #column headers
    while True: #an infinite loop
        connectionSocket, addr = serverSocket.accept()  #Try to accept incoming connection-requests
        thread.start_new_thread(handleClient, (connectionSocket, addr)) #make a new thread with this new client


def client(arguments):

 
    print("\nID\t\t\tInterval\tTransfer\tBandwidth\n")              #prints the column headers

    
   
    """
    if arguments.parallel > 1:      #if there are parallel connections
        for i in range(arguments.parallel):                                         #iterate through every connection
            clientSyncer(connections["client_sd{0}".format(i)], "ACK:BYE", "BYE")  #Synch every connection to the server and send a BYE-message
    else:                           #if there are only one connection
        clientSyncer(connections["client_sd0"], "ACK:BYE", "BYE")  #synch this one connection to the server and send a BYE-message
    """   
    
    #closing of all client connections
    if arguments.parallel > 1:                              #if the number of parallel connections is greater than 1
        for i in range(arguments.parallel):                 #iterate through every connection
            connections["client_sd{0}".format(i)].close()   #close every connection
    else:                                                   #if the number of parallel connections is 1
        connections["client_sd0"].close()                   #close this single connection
    
parser = argparse.ArgumentParser(description="Optional Arguments")    #Title in the -h menu over the options available

#Adds options to the program
parser.add_argument("-s", "--server", action="store_true", help="Assigns server-mode")                                          #Server specific
parser.add_argument("-c", "--client", action="store_true", help="Assigns client-mode")                                          #Client specific
parser.add_argument("-p", "--port", default="8088", type=check_port, help="Allocate a port number")                             #Server and Client specific
parser.add_argument("-I", "--serverip", type=check_ip, default="127.0.0.1", help="Set IP-address of server from client")        #Client specific
parser.add_argument("-b", "--bind", type=check_ip, default="127.0.0.1", help="Set IP-address that client can connect to")       #Server specific
parser.add_argument("-r", "--reliability", type=check_reliability, default=None, help="Choose reliability-mode")                #Client specific
parser.add_argument("-f", "--file", type=check_file, default="default.jpg", help="Choose file to send over")                    #Client specific
parser.add_argument("-m")

arguments=parser.parse_args()       #gathers all the options into a list

if arguments.server or arguments.client:        
    if arguments.server and arguments.client:   #if the user has used both -s and -c
        print("Error: you cannont run this program in both server and client mode at the same time")    #Error-message cannot be both server and client
        sys.exit()                              #exits the program
    if arguments.server:                        #if -s is used
        print("-----------------------------------------------\n",
              "A simpleperf server is listening on port", arguments.port,       #print a header on the server side
              "\n-----------------------------------------------\n")
        server(arguments)                       #go into server mode
    if arguments.client:                        #if -c is used
        print("---------------------------------------------------------------\n",
              "A simpleperf client connecting to server", arguments.serverip, "port", arguments.port, #print a header on the client side
              "\n---------------------------------------------------------------\n")
        client(arguments)                       #go into client mode

else:       #if neither -c or -s is used
    print("Error: you must run either in server or client mode")    #print error you must choose
    sys.exit()          #exit program   
