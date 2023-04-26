import argparse
import sys
import ipaddress
from socket import *
import _thread as thread
from threading import Thread
import pickle
import time
import random

'''
    #Utility functions: 1) to create a packet of 1472 bytes with header (12 bytes) (sequence number, acknowledgement number,
    #flags and receiver window) and applicaton data (1460 bytes), and 2) to parse
    # the extracted header from the application data. 
'''


"""--------------------------Guide to socket communication and packet assembly/extraction-------------------------------
Send over socket:
clientSocket.sendto(<packagename>, (str(arguments.serverip), arguments.port))
serversocket.sendto(<packagename>, (str(arguments.serverip), arguments.port))

recieve from socket:
<packagename> = serverSocket.recv(1000)

Extract header from packet:
<headername> = <packetname>[:12]

Extract header variables from header:
seq, acknr, flags, win = parse_header(<headername>)

Extract flag variables from flags:
syn, ack, fin = parse_flags(flags)

Create a packet:
create_package(seq, acknr, flags, win, data)
    Arguments:
        seq = Sequence number, the id of the package in the right order
        acknr = Acknowledgement number, the id of the package recieved in the right order
        flags = a number which is converted into bit-number marking the flags syn, ack, fin, reset (reset is never used)
                for eksample:   if flags = 4, then the corresponding bit-number is 0 1 0 0. 
                                comparing 0 1 0 0 to syn, ack, fin, reset, shows us that the ack-flag is turned on
                syn = Syncronize, a flag that can either be 0 or 1 signaling a request to syncronize client and server
                ack = Acknowledge, a flag that can either be 0 or 1 informing the other part that the previous message was recieved
                fin = Finished, a flag that can be either 0 or 1 informing the other part that this is the last message sent
                reset = Reset, never used...
        win = Window size, the size of the buffer size the server has to operate with. Whenever server sends a packet this should be 5, otherwise 0.

Extract data from file
    with open('checkerboard.jpg', 'rb') as f:
        # Read 1460 bytes from the image file
        data = f.read(1460)
"""

from struct import *

# I integer (unsigned long) = 4bytes and H (unsigned short integer 2 bytes)
# see the struct official page for more info

header_format = '!IIHH'             #("(4), (4), (2), (2)")

#print the header size: total = 12
#print (f'size of the header = {calcsize(header_format)}')


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
    #print (f'Create_packet(72): packet containing header + data, is {len(packet)} bytes long') #just to show the length of the packet
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
    #using rest in our implementation
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin

def test_create_packet():
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
    #which unpacks the values based on the header_format that we specified
    seq, ack, flags, win = parse_header (header_from_msg)
    print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')

    #let's extract the data_from_msg that holds
    #the application data of 1460 bytes
    data_from_msg = msg[12:]
    print (len(data_from_msg))

def test_ack_packet():
    #let's mimic an acknowledgment packet from the receiver-end
    #now let's create a packet with acknowledgement number 1
    #an acknowledgment packet from the receiver should have no data
    #only the header with acknowledgment number, ack_flag=1, win=5
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
    seq, acknr, flags, win = parse_header (msg) #it's an ack message with only the header
    print(f'seq={seq}, acknr={acknr}, flags={flags}, receiver-window={win}')

    #now let's parse the flag field
    syn, ack, fin = parse_flags(flags)
    print (f'syn_flag = {syn}, fin_flag={fin}, and ack_flag={ack}')


"""-----------------------------------------------------------------------------------------------------"""

def server_stop_and_wait(serverSocket):
    #lag en while løkke som kjører så lenge inkommende melding ikke inkluderer et fin-flag
    """while loop here and indent the code below"""

    #server lytter etter client sin message
    recieved_msg = serverSocket.recv(1000)
    
    #server henter ut de 12 første bytes, og kaller den for header
    recieved_header = recieved_msg[:12]
    
    #kaller funksjonen som fordeler headeren i forskjellige deler: sequence number, acknowledgement number, flags, window size.
    #Lager variabler som tilsvarer dette
    seq, acknr, flags, win = parse_header(recieved_header)
    
    #kaller funksjonene som fordeler flags i ulike variabler
    syn, ack, fin = parse_flags(flags)

    #server skal sjekke om sequence number (seq), er riktig
    #dvs. første gang skal den være 1, andre gang skal den være 2 osv.
    """
    if sequence number is correct
        create a package with sequence number (seq) = 0, acknowledge number (ack) = recieved sequence number, bytenumber in flags, windowsize = 0, data = b''
        send this package to the client (linje: 19)
        update sequence number
    else:
        print en error melding
    """
    return 0
def client_stop_and_wait(clientSocket, arguments):
    """ Kode for å hente data fra en fil:
    with open('checkerboard.jpg', 'rb') as f:
        # Read 1460 bytes from the image file
        data = f.read(1460)
    """
    
    #lag en while løkke som looper så lenge det er data i filen
    """while loop with the code under inside"""
    send_packet = create_packet(1, 0, 0, 0, data)
    clientSocket.sendto(send_packet, (str(arguments.serverip), arguments.port))
    #når det ikke er mer data å hente ut ifra bildet, skru på fin-flagget og avslutt funksjonen
    
    #placeholder
    return 0


#Genie AI
'''
def go_back_n(data, clientSocket, connectionSocket):
    # Set up socket
    sock = connectionSocket
    sock.settimeout(0.5)

    window_size = 5
    base = 1
    next_seq_num = 1

    # Split data into packets
    packets = [data[i:i+10] for i in range(0, len(data), 10)]

    while base <= len(packets):
        # Send packets within window
        while next_seq_num < base + window_size and next_seq_num <= len(packets):
            packet = str(next_seq_num) + packets[next_seq_num-1]
            sock.sendto(packet.encode(), clientSocket)
            next_seq_num += 1

        try:
            # Receive ACKs
            data, clientSocket = sock.recvfrom(1024)
            ack = int(data.decode())
            if ack >= base:
                base = ack + 1
        except socket.timeout:
            # Timeout - retransmit packets
            next_seq_num = base
    sock.close()
'''
#WINDOW_SIZE = 6400
#BUFFER_SIZE = 4096 (recv-value ellerno)
'''
def client_go_back_n(sock, address, data):
    n_packets = len(data)
    next_seq_num = 0
    base_seq_num = 0
    window_size = min(WINDOW_SIZE, n_packets)

    while base_seq_num < n_packets:
        # Send packets within the window
        while next_seq_num < base_seq_num + window_size:
            pkt = create_packet(next_seq_num, -1, 0, window_size, data[next_seq_num])
            send_packet(sock, pkt, address)
            next_seq_num += 1

        # Wait for ACK with matching sequence number
        try:
            ack_packet, addr = sock.recvfrom(BUFFER_SIZE)
            ack_seq_num, _, ack_flags, _, _ = parse_header(ack_packet)

            # Update window based on ACK number
            if base_seq_num <= ack_seq_num < next_seq_num:
                base_seq_num = ack_seq_num + 1
                window_size = min(WINDOW_SIZE, n_packets - base_seq_num)
        
        except socket.timeout:
            # Resend packets within the window
            next_seq_num = base_seq_num

    # Send EOT packet to signal end of transmission
    eot_pkt = create_packet(base_seq_num, -1, 1, window_size, b'')
    send_packet(sock, eot_pkt, address)
'''
def server_selective_repeat():
    return 0
def client_selective_repeat():
    return 0


"""
----------------------------------------------------------------------------------------------------
CONTENT FOR READING IMAGE FILE AND EXTRACTING IT
"""
'''
# Define the necessary constants
SERVER_ADDRESS = ('localhost', 8000)
BUFFER_SIZE = 1460  # update buffer size to 1460 bytes
PACKET_HEADER = struct.pack('!IIHH', 0, 0, 0, 0)   # create packet header !IIHH
MAX_PACKET_SIZE = 1472

# Open the image file
with open('filename.jpg', 'rb') as f:
    # Read 1460 bytes from the image file
    data = f.read(BUFFER_SIZE)

    # create a packet with updated header and send it using GBN
    seq_number = 0
    while data:
        payload_size = len(data)
        if payload_size + struct.calcsize(PACKET_HEADER) > MAX_PACKET_SIZE:
            payload_size = MAX_PACKET_SIZE - struct.calcsize(PACKET_HEADER)

        # create packet with new payload
        packet_data = PACKET_HEADER + data[:payload_size]
        
        # send packet using GBN
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.sendto(packet_data, SERVER_ADDRESS)
            ack, _ = s.recvfrom(1024)
            if ack == seq_number:
                seq_number += 1
                data = f.read(BUFFER_SIZE)
        except socket.timeout:
            pass
        finally:
            s.close()
'''
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


def check_file(val):
    #Check-code goes here (vet ikke om dette er nødvendig i det hele tatt)
    return val

def serverSyncer(connectionSocket, recvWord, sendWord):        # may need to remove this
    while True:     #infinite loop untill 'break'
        connectionSocket.send(sendWord.encode())        #send the sendWord to client
        message = connectionSocket.recv(99999).decode() #recieve everything that the client sendt
        if recvWord in message:                        
            print(recvWord)                            
            break                                      
        else:
            continue

def clientSyncer(client_sd, recvWord, sendWord):         # may need to remove this
    while True:    
        message = client_sd.recv(2048).decode() 
        if recvWord in message:                
            client_sd.send(sendWord.encode())   
            print(recvWord)                     
            break                              
                                

def server(arguments): 
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    try:
        serverSocket.bind((str(arguments.bind), arguments.port))   
    except:
        print("Bind failed - Wait and try again, or check if the IP-address is supported") 
        sys.exit()                                                                         
    
    
    while True: #an infinite loop
        data = serverSocket.recv(2048)  #recieve message with pickle with client-options
        client_options = pickle.loads(data) #retrieves the client-options (unpacking)

        #Three-way-handshake
        time_out = 1
        serverSocket.settimeout(int(time_out))

        client_syn, clientAddress = serverSocket.recvfrom(1000)
        header_from_msg = client_syn[:12]
        seq, acknr, flags, win = parse_header(header_from_msg)
        syn, ack, fin = parse_flags(flags)
        print("\nServer: Header information from recieved SYN package:\n\tSequence number:", seq, "\n\tAcknowledgement number:", acknr,
                  "\n\tFlags:\n\t\tsyn:", syn, "\n\t\tack:", ack,"\n\t\tfin:", fin, "\n\tWindow size:", win)
        
        if syn > 0 and ack == 0 and fin == 0 and seq == 1 and acknr == 0:
            msg = create_packet(2, 1, 12, 0, b'')
            serverSocket.sendto(msg, clientAddress)
            client_ack, clientAddress = serverSocket.recvfrom(1000)
            header_from_client_ack = client_ack[:12]
            seq, acknr, flags, win = parse_header(header_from_client_ack)
            syn, ack, fin = parse_flags(flags)
            print("Server: Header information from recieved ACK package:\n\tSequence number:", seq, "\n\tAcknowledgement number:", acknr,
                  "\n\tFlags:\n\t\tsyn:", syn, "\n\t\tack:", ack,"\n\t\tfin:", fin, "\n\tWindow size:", win)
            if ack > 0 and syn == 0 and fin == 0 and seq == 3 and acknr == 2:
                break
            else:
                raise ConnectionError("ACK-message from client unsuccsessful")
        else:
            raise ConnectionError("SYN-request from client unsuccsessful")

    #if test som velger hvilken modus serveren skal kjøre i
    if client_options.reliability == "gbn":
        print("The client chose Go back N")
        client_go_back_n()
    elif client_options.reliability == "saw":
        print("The client chose Stop and wait")
        client_stop_and_wait()
    elif client_options.reliability == "sr":
        print("the client chose selective repeat")
        client_selective_repeat()

def client(arguments):
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    data_string = pickle.dumps(arguments)
    clientSocket.sendto(data_string, (str(arguments.serverip), arguments.port))

    # Three-way-handshake
    time_out = 10
    clientSocket.settimeout(int(time_out))
    msg = create_packet(1, 0, 8, 0, b'')  # SYN message
    clientSocket.sendto(msg, (str(arguments.serverip), arguments.port))
    while True:
        try:
            message, serverAddress = clientSocket.recvfrom(2048)  # SYN-ACK message
            header_from_msg = message[:12]
            seq, acknr, flags, win = parse_header(header_from_msg)
            syn, ack, fin = parse_flags(flags)
            print("\nClient: Header information from recieved SYN:ACK package:\n\tSequence number:", seq, "\n\tAcknowledgement number:", acknr,
                  "\n\tFlags:\n\t\tsyn:", syn, "\n\t\tack:", ack,"\n\t\tfin:", fin, "\n\tWindow size:", win)
            
            if syn > 0 and ack > 0 and fin == 0 and seq == 2 and acknr == 1: # Check if sequence number matches.
                seq += 1
                acknr += 1
                break  
        except timeout:
            raise ConnectionError("SYN-ACK from server unsuccessful")
    print("seq:", seq, "acknr", acknr)        
    msg = create_packet(seq, acknr, 4, 0, b'')  # ACK message
    clientSocket.sendto(msg, serverAddress)
    # Successfull 3 way handshake completed.
    
    #Figuring out which reliability function the transfer is going to use
    if arguments.reliability == "gbn":
            print("The client chose Go back N")
            client_go_back_n()
    elif arguments.reliability == "saw":
            print("The client chose Stop and wait")
            client_stop_and_wait(clientSocket, arguments)
    elif arguments.reliability == "sr":
            print("the client chose selective repeat")
            client_selective_repeat()

     
    
    
parser = argparse.ArgumentParser(description="Optional Arguments")    #Title in the -h menu over the options available

#Adds options to the program
parser.add_argument("-s", "--server", action="store_true", help="Assigns server-mode")                                          #Server specific
parser.add_argument("-c", "--client", action="store_true", help="Assigns client-mode")                                          #Client specific
parser.add_argument("-p", "--port", default="8088", type=check_port, help="Allocate a port number")                             #Server and Client specific
parser.add_argument("-I", "--serverip", type=check_ip, default="127.0.0.1", help="Set IP-address of server from client")        #Client specific
parser.add_argument("-b", "--bind", type=check_ip, default="127.0.0.1", help="Set IP-address that client can connect to")       #Server specific

parser.add_argument("-r", "--reliability", type=str, choices=("gbn", "saw", "sr"), default=None, help="Choose reliability-mode")                #Client specific
parser.add_argument("-f", "--file", type=check_file, default="default.jpg", help="Choose file to send over")                    #Client specific


arguments=parser.parse_args()       #gathers all the options into a list

if arguments.server or arguments.client:        
    if arguments.server and arguments.client:   #if the user has used both -s and -c
        print("Error: you cannont run this program in both server and client mode at the same time")    #Error-message cannot be both server and client
        sys.exit()                              #exits the program
    
    if arguments.server:                        #if -s is used
        server(arguments)                       #go into server mode
    if arguments.client:                        #if -c is used
        client(arguments)                       #go into client mode

else:       #if neither -c or -s is used
    print("Error: you must run either in server or client mode")    #print error you must choose
    sys.exit()          #exit program   
