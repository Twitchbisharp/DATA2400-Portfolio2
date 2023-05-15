import argparse
import os
import sys
import ipaddress
from socket import *
import _thread as thread
from threading import Thread
import pickle
import time
import random
from math import *
from datetime import datetime
from struct import *


header_format = '!IIHH'             #("(4), (4), (2), (2)")

def create_packet(seq, ack, flags, win, data):
    header = pack (header_format, seq, ack, flags, win)
    packet = header + data
    return packet


def parse_header(header):
    header_from_msg = unpack(header_format, header)
    return header_from_msg
    

def parse_flags(flags):
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin

def test_create_packet():
    print ('\n\ncreating a packet')

    data = b'0' * 1460
    print (f'app data for size ={len(data)}')

    sequence_number = 1
    acknowledgment_number = 0
    window = 0 
    flags = 0 

    msg = create_packet(sequence_number, acknowledgment_number, flags, window, data)

    header_from_msg = msg[:12]
    print(len(header_from_msg))

    seq, ack, flags, win = parse_header (header_from_msg)
    print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')

    data_from_msg = msg[12:]
    print (len(data_from_msg))

def test_ack_packet():
    data = b'' 
    print('\n\nCreating an acknowledgment packet:')
    print (f'this is an empty packet with no data ={len(data)}')

    sequence_number = 0
    acknowledgment_number = 1
    window = 0
    flags = 4 

    msg = create_packet(sequence_number, acknowledgment_number, flags, window, data)
    print (f'this is an acknowledgment packet of header size={len(msg)}')

    seq, acknr, flags, win = parse_header (msg)
    print(f'seq={seq}, acknr={acknr}, flags={flags}, receiver-window={win}')

    syn, ack, fin = parse_flags(flags)
    print (f'syn_flag = {syn}, fin_flag={fin}, and ack_flag={ack}')


###
#   All "_" are just random names to progress the code without an update in value
###
# SERVER ----------------------
def server_go_back_n(serverSocket, arguments, client_options):
    print("Server Go-Back-N")
    #print("\nNew window count:  1")

    window_size = client_options.windowSize
    fin = 0
    allMessages = []
    seqnr = 0
    new_window = 1
    print("\nNew window count: ", str(new_window))
    
    while fin != 2:
        print("New window of " + str(window_size) + " packets created\n")
        window_messages = [None] * window_size
    
        for i in range(window_size):
            try:
                msg, reciever = serverSocket.recvfrom(2048)
            except timeout:
                print("timeout")
                break
            
            seq, ack, flags, win = parse_header(msg[:12])
            syn, ackflag, fin = parse_flags(flags)
            print("HERE IS SEQ: ", seq)
            window_messages[i] = msg 
            seqnr += 1

            if fin == 2:
                break
    
        # send cumulative acknowledgment for last received packet
        if window_messages[window_size - 1] is not None:
            seq, ack, flags, win = parse_header(window_messages[window_size - 1][:12])
            syn, ackflag, fin = parse_flags(flags)
            ackpkt = create_packet(0, seq, 0, window_size, b'')
            serverSocket.sendto(ackpkt, reciever)
            print("Sending ACK for packet with seq up to " + str(seq))
        
        allMessages.extend(window_messages)
        print("Finished sending ACK")
        new_window +=1
        print("\nNew window count: ", str(new_window))
    
    datalist = []
    for i in allMessages:
        if i == None:
            continue
        else:
            data = i[12:]
            datalist.append(data)
    with open(arguments.destination, 'wb') as f:   
        for i in datalist:
            f.write(i) 
        
### CLIENT ----------------------
def client_go_back_n(clientSocket, arguments):
    print("Client Go-Back-N")

    fin = 0
    next_seqnum = 1
    datalength = 0
    sent_packets = []
    seq = 0
    int(seq)
    new_window = 1

    last_ack = 0
    while fin != 2:

        print("\nFIN ==", fin)
        print("New window count: ", str(new_window))
        windowIndex = 1
        #sending data
        for i in range(next_seqnum, min(next_seqnum + arguments.windowSize, last_ack + arguments.windowSize + 1)):
            seq += 1
            with open(arguments.file, "rb") as name:
                f = name.read()[datalength:(datalength+1460)]
                b = bytes(f)
                print("From:", datalength, "To:", datalength+1460, "Difference:", len(b), "b sin length", len(b))
                if len(b) < 1460:
                    fin = 2
                    
            #PACKET LOSS GENERATOR
            if arguments.test_case == "loss" and seq == 8:   #If the client specified that it wants to deliberatley drop a package
                                       
                print("^\tThis packet is skipped (", seq,")")     #Output print
                continue
            #END PACKET LOSS GENERATOR

            datalength += 1460
            msg = create_packet(seq, 0, fin, arguments.windowSize, b)

            clientSocket.sendto(msg, (str(arguments.serverip), arguments.port)) 
            print("Sent packet nr:", seq, "with window-index.", windowIndex, "\n")
            sent_packets.append((i, msg))
            windowIndex += 1   

        try:
            recpkt, reciever = clientSocket.recvfrom(2048)
            _, acknr, flags, win = parse_header(recpkt)
            syn, ackflag, fin = parse_flags(flags)

            if acknr > last_ack:
                last_ack = acknr

            print("Recieved ACK for packet with seq up to " + str(acknr))
        except timeout:
            print("timeout, resending window")
            print("here is seq", seq)
            seq -= 5

            continue

        new_window += 1
    print("Finished sending packets\n")


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
    return val

def check_windowSize(val):
    int(val)
    if val < 5 and val > 15:
        raise argparse.ArgumentTypeError("The windowsize should only be between 5 and 15")
    else:
        return val

def server(arguments): 
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    try:
        serverSocket.bind((str(arguments.bind), arguments.port))   
    except:
        print("Bind failed - Wait and try again, or check if the IP-address is supported") 
        sys.exit()
    
    while True:
        data = serverSocket.recv(2048)  #recieve message with pickle with client-options
        client_options = pickle.loads(data) #retrieves the client-options (unpacking)

        #Three-way-handshake
        time_out = .5
        serverSocket.settimeout(time_out)

        client_syn, clientAddress = serverSocket.recvfrom(1000)
        header_from_msg = client_syn[:12]
        seq, acknr, flags, win = parse_header(header_from_msg)
        syn, ack, fin = parse_flags(flags)
        
        if syn > 0 and ack == 0 and fin == 0 and seq == 1 and acknr == 0:
            msg = create_packet(0, 1, 12, 0, b'')
            serverSocket.sendto(msg, clientAddress)
            client_ack, clientAddress = serverSocket.recvfrom(1000)
            header_from_client_ack = client_ack[:12]
            seq, acknr, flags, win = parse_header(header_from_client_ack)
            syn, ack, fin = parse_flags(flags)

            if ack > 0 and syn == 0 and fin == 0 and seq == 2 and acknr == 2:
                break
            else:
                raise ConnectionError("ACK-message from client unsuccsessful")
        else:
            raise ConnectionError("SYN-request from client unsuccsessful")

    #if test som velger hvilken modus serveren skal kjøre i
    if client_options.reliability == "gbn":
        print("The client chose Go back N")
        server_go_back_n(serverSocket, arguments, client_options)

def client(arguments):
    start_time = time.time()
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    data_string = pickle.dumps(arguments)
    clientSocket.sendto(data_string, (str(arguments.serverip), arguments.port))

    # Three-way-handshake
    time_out = 5
    clientSocket.settimeout(time_out)
    msg = create_packet(1, 0, 8, 0, b'')  # SYN message
    clientSocket.sendto(msg, (str(arguments.serverip), arguments.port))
    while True:
        try:
            message, serverAddress = clientSocket.recvfrom(2048)  # SYN-ACK message
            header_from_msg = message[:12]
            seq, acknr, flags, win = parse_header(header_from_msg)
            syn, ack, fin = parse_flags(flags)
            
            if syn > 0 and ack > 0 and fin == 0 and seq == 0 and acknr == 1: # Check if sequence number matches.
                seq = acknr+1
                acknr = acknr+1
                break  
        except timeout:
            raise ConnectionError("SYN-ACK from server unsuccessful")       
    msg = create_packet(seq, acknr, 4, 0, b'')  # ACK message
    clientSocket.sendto(msg, serverAddress)
    # Successfull 3 way handshake completed.
    
    #Figuring out which reliability function the transfer is going to use
    if arguments.reliability == "gbn":
            print("The client chose Go back N")
            client_go_back_n(clientSocket, arguments)
    
    end_time = time.time()  # stop timer
    elapsed_time = end_time - start_time
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.6f} seconds.")
    try:
        pass
    finally:
        file_size_bytes = os.path.getsize('output.txt')
        print("FileSize: ", file_size_bytes)
        bytes_per_second = file_size_bytes / elapsed_time
        mBytes_per_second = bytes_per_second / 1000000
        print(f"Bytes per second: {bytes_per_second:.2f}")
        print(f"MegaBytes per second: {mBytes_per_second:.2f}")
    
parser = argparse.ArgumentParser(description="Optional Arguments")    #Title in the -h menu over the options available
#Adds options to the program
parser.add_argument("-s", "--server", action="store_true", help="Assigns server-mode")
parser.add_argument("-c", "--client", action="store_true", help="Assigns client-mode")
parser.add_argument("-p", "--port", default="8088", type=check_port, help="Allocate a port number") 
parser.add_argument("-I", "--serverip", type=check_ip, default="127.0.0.1", help="Set IP-address of server from client") 
parser.add_argument("-b", "--bind", type=check_ip, default="127.0.0.1", help="Set IP-address that client can connect to")  

parser.add_argument("-w", "--windowSize", type=int, default=5, help="Specify window size")
parser.add_argument("-r", "--reliability", type=str, choices=("gbn", "saw", "sr"), default=None, help="Choose reliability-mode")
parser.add_argument("-f", "--file", type=check_file, default="checkerboard.jpg", help="Choose file to send over") 
parser.add_argument("-d", "--destination", type=str, default="output.jpg", help="Choose destination file")
parser.add_argument("-t", "--test_case", type=str, choices=("loss", "drop_ack"), default=None, help="Choose test case")

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

