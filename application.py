import argparse
import sys
import ipaddress
from socket import *
import _thread as thread
from threading import Thread
import pickle
import time
import os
import random
import math
from struct import *

"""
Regarding GBN, the code itself is able to transfer both text and image, but that is only the case for the older version of the code. The version where we “gracefully closed the connection” did not exist.
On the server this would be…

    data, reciever = serverSocket.recvfrom(2048) # Change this to “data = serverSocket.recv(2048)”
    closing the connection gracefully
        msg = create_packet(0,0,4,0,b'')
        serverSocket.sendto(msg, reciever)
        print("\nGracefully closed the connection")
        serverSocket.close()

On the client this would be…

    closing the connection gracefully
        finalACK = clientSocket.recv(2048)
        syn, acknr, flags, win = parse_header(finalACK[:12])
        seq, ack, fin = parse_flags(flags)
        if ack == 4:
            print("\nGracefully closed the connection")
            clientSocket.close()
"""

header_format = '!IIHH'   

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

###################### ADARSH START #####################
def server_stop_and_wait(serverSocket, arguments, client_options):
    print("Server Stop-and-Wait")

    fin = 0
    seqnum = 1
    prev_seqnum = 0
    allMessages = []

    while fin != 2:
        try:
            msg, reciever = serverSocket.recvfrom(2048)
        except timeout:
            print("Timeout, resending ACK for packet with seq " + str(prev_seqnum))
            ackpkt = create_packet(0, prev_seqnum, 0, 1, b'')
            serverSocket.sendto(ackpkt, reciever)
            continue
        
        seq, ack, flags, win = parse_header(msg[:12])
        syn, ackflag, fin = parse_flags(flags)

        if seq == seqnum:
            allMessages.append(msg)
            seqnum += 1
            prev_seqnum = seq
        #deliberate ack loss
        if seq == 2 and client_options.test_case == "drop_ack":
                print("\n\nDropped ACK packet for nr 2")
                continue

        ackpkt = create_packet(0, prev_seqnum, 0, 1, b'')
        serverSocket.sendto(ackpkt, reciever)
        print("Sending ACK for packet with seq " + str(prev_seqnum))

    datalist = []
    for i in allMessages:
        data = i[12:]
        datalist.append(data)
    with open(arguments.destination, 'wb') as f:   
        for i in datalist:
            f.write(i) 

def client_stop_and_wait(clientSocket, arguments):
    print("Client Stop-and-Wait")

    fin = 0
    seqnum = 1
    datalength = 0

    while fin != 2:
        with open(arguments.file, "rb") as name:
            f = name.read()[datalength:(datalength+1460)]
            b = bytes(f)
            if len(b) < 1460:
                fin = 2
        datalength += 1460
        msg = create_packet(seqnum, 0, fin, 1, b)

        if seqnum == 11 and arguments.test_case == "loss":
            print("Deliberate packet loss")
            seqnum +=1
            continue
        
        msg = create_packet(seqnum, 0, fin, 1, b)
        clientSocket.sendto(msg, (str(arguments.serverip), arguments.port)) 
        print("Sent packet nr:", seqnum, "\n")


        try:
            recpkt, reciever = clientSocket.recvfrom(2048)
            _, acknr, flags, win = parse_header(recpkt)
            print("Received ACK for packet with seq " + str(seqnum))
            seqnum += 1
        except timeout:
            print("Timeout, resending packet")
            clientSocket.sendto(msg, (str(arguments.serverip), arguments.port)) 
            seqnum += 1
            print ("seq er ", seqnum)
            continue
    print("Finished sending packets\n")
    print("Client Stop-and-Wait")


################### ADARSH END ########################


################### WILLIAM START ###################
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
            #print("HERE IS SEQ: ", seq)
            window_messages[i] = msg 
            seqnr += 1

            if fin == 2:
                break
            
            #PACKET LOSS GENERATOR
            if client_options.test_case == "drop_ack" and seq == 7:   #If the client specified that it wants to deliberatley drop a package
                                       
                print("^\tThis ACK is dropped (", seq,")")     #Output print
                continue
            #END PACKET LOSS GENERATOR
            print("HERE IS SEQ: ", seq)

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
    with open(client_options.destination, 'wb') as f:   
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
    print("Client Go-Back-N")

################# WILLIAM END ###################

################# FILIP START ##################   
# Description
# Server side code for reliability function Selective Repeat
# Arguments:
#   serverSocket:   The socket of the server
#   arguments:      The options specified when starting the server
#   client_options: The options specified when starting the client
# Returns: Nothing
def server_selective_repeat(serverSocket, arguments, client_options):
    print("Server Selective Repeat")        #Output print
    
    window_size = client_options.windowSize #Creates an alias for window size
    fin = 0                                 #Sets fin-flag to 0
    allMessages = []                        #Create a list of all recieved messages with data
    seq = 0                                 #Initializes sequence number
    seqnr = 0                               #Initializes sequence number for exception handeling
    reciever = (None, None)                 #Create a tuple for the reciever address
    while fin != 2:                         #Main loop until all packets gets recieved
        print("\n\nStart of new loop")      #Output print
        print("New window of", client_options.windowSize,"packets created") #Output print
        window_messages = [None] * window_size      #Creates a list containing all the packets in a given window
        
        
        for i in range(window_size):                #Iterates through the window
            if seq >= seqnr:                        #If test for whoever has the highest (most recent) value of sequence number
                oldseq = seq
            elif seqnr > seq:
                oldseq = seqnr
            try:
                serverSocket.settimeout(.7)         #Sets the timeout window to be higher than the clients
                msg, reciever = serverSocket.recvfrom(2048) #Try to recieve packets with data from client
            except timeout:                         #if no packet gets recieved
                break                               #break and continue with one packet less
            
            seq, ack, flags, win = parse_header(msg[:12])   #Unpack the packet (can be)
            syn, ackflag, fin = parse_flags(flags)          #Unpack the header
            diff = seq - oldseq                             #find the difference in sequence number between this packet and the previous
            print("Got packet nr:", seq,":\t\toldseq:", oldseq, "\tseq:", seq, "\tdiff:",diff)  #Output print
            
            if diff == 1:                                                           #If this is true, the packet came in sequence
                window_messages[((seq-1)%client_options.windowSize)] = msg          #Places recieved message in correct window_messages-list, indexing makes it seq-1
            else:                                                                   #If packet came out of order/lost
                window_messages[((oldseq-1)%client_options.windowSize)+diff] = msg  #Place recieved message where the packet should of been

        ###ACK SENDING
        print("\nACK sending")  #Output print             
        errors = -1             #Create variable for the amount of errors in recieved packets
        skipped = 0             #Create variable for if ACKs are skipped
        firstTime = True        #Flag-lock for not resending a new window of empty packages
        while errors != 0:      #While there are no errors in the window messages list
            #ERROR RETRANSMISSION LOOP
            for i in range(errors):     #Iterates through all errors
                print("\nerrors left:", errors)     #Output print
                retransmit, reciever = serverSocket.recvfrom(2048)  #Recieves a new package from client      
                seqnr, ack, flags, win = parse_header(retransmit[:12])  #Retrieves sequence number      
                syn, ackflag, fin = parse_flags(flags)                  #Retrieves fin-flag
                print("Recieved retransmit seq:", seqnr)                #Output print
                
                window_messages[(seqnr%client_options.windowSize)-1] = retransmit   #Updates the packages in window messages list to contain the correct package at the correct place             
                
                reack = create_packet(0,seqnr,fin,window_size, b'reack')    #Creates a new ACK package for the newly recieved retransmitted package
                serverSocket.sendto(reack, reciever)                        #Sending it to client
                errors-=1                                                   #Resolved one error, decrements error value
            errors = 0                                       #First loop changes errors from -1 to 0
            #END ERROR RETRANSMISSION LOOP

            flag = True                                     #Flag-lock for DROP_ACK GENERATOR to only happen once
            if firstTime == True:                           #If test to prevent resending of a window with no data
                for i in range(client_options.windowSize):  #Iterates through the size of the window
                    if window_messages[i] == None:          #if packet isn't recieved       
                        retransmit = create_packet(0,seq,fin,window_size,b'')   #Create a retransmit packet
                        serverSocket.sendto(retransmit, reciever)               #Send this request to client
                        print("sent loss error:", i+1)                          #Output print
                        errors +=1                          #Update the number of errors, enters ERROR RETRANSMISSION LOOP after this
                    else:                                                               #If a packet gets recieved normally
                        seq, ack, flags, win = parse_header(window_messages[i][:12])    #Finds current sequence number
                        syn, ackflag, fin = parse_flags(flags)                          #Updates the fin-flag

                        msg = create_packet(0,seq, fin, client_options.windowSize, b'') #Create a ACK-header

                        #DROP_ACK GENERATOR
                        if flag == True and client_options.test_case == "drop_ack" and seq == 3: #If the client wants to deliberately drop an ACK 
                            flag = False                #Prevent this if to happen again
                            print("Skipped ack:", seq)  #Output print
                            skipped+=1                  #Update amount of skipeed ACKs
                        else:                           #If no ACKs should be dropped
                            serverSocket.sendto(msg, reciever)  #Sends the ACK packet
                            print("sent acknr:", seq)           #Ouput print
                firstTime = False                       #Prevent this if to happen again
            
         
        
                        
                    
        allMessages.extend(window_messages)     #Place all messages in window messages in the list allMessages
        print("finished sending acks")          #Ouput print
        
        if client_options.test_case == "drop_ack":  #If the client wants to deliberately drop an ack
            while skipped > 0:      #Iterates through the amount of skipped ACKs
                try:
                    print("\tRecieved retransmission request from client")  #Output print
                    message, reciever = serverSocket.recvfrom(2048)         #Recieve retransmit ACK request from client
                    seqnr, ack, fin, win = parse_header(message[:12])       #Unpack to check what ACK number it should be
                    msg = create_packet(0,seqnr,fin,win,b'resendtACK')      #Creates corresponding ACK header
                    serverSocket.sendto(msg, reciever)                      #Sends this ACK to client
                    print("\tSending ack",seqnr,"again")                    #Ouput print
                    skipped -=1                                             #Decrement the amount of skipped acks
                except timeout:                                             #If the connection times out
                    break                                                   #Exit the loop, no more resendings needed
        print("\nCurrent status of flags:\tsyn:", syn, "ack", ackflag,"fin", fin)   #Ouput print
        print("------------------------------------------------------------------") #Ouput print
        if fin == 2:                            #If fin-flag is 2
            print("That was last window...")    #Output print
    
    datalist = []           #Create a list of the recieved data
    for i in allMessages:   #Iterate through the list allMessages
        data = i[12:]       #Retireve data from packet
        datalist.append(data)   #Palce the data in datalist
    #with open(client_options.destination, 'w') as f:    #Open a new file
    #    for i in datalist:                              #Iterate through the list datalis
    #        f.write(str(repr(i)[2:-1]))                 #Paste the data from datalist to the new file
    with open(client_options.destination, 'wb') as f:
        for i in datalist:
            f.write(i)
    
# Description
# Client side code for reliability function Selective Repeat
# Arguments:
#   clientSocket:   The socket of the client
#   arguments:      The options specified when starting the client
# Returns: Nothing
def client_selective_repeat(clientSocket, arguments):
    print("Client Selective Repeat")
    fin = 0             #The fin flag that tells if the client is finished sending
    roundnr = 1         #Specifies the number of loops the outermost while loop has iterated through       
    datalength = 0      #The length of how much data has been read from the input-file
    seqnr = 1           #The sequence number of a given package
    flag = True         #A flag-locker that ensures that only one packet gets dropped
    while fin != 2:     #The main while loop for client-side transmission. Stops when fin-flag is on
        print("\nStart of loop", roundnr,"\nFIN-flag is currently: FIN ==", fin, "\n")        #Output print
        sent_packets = [None] * arguments.windowSize            #Creates a list of None-elements with a length equal to the specified window size
        windowIndex = (seqnr-1)%(arguments.windowSize)          #Creates a variable for the index of where the packets shall go
        
        ####START SENDING DATA
        print("SENDING PACKETS:\n----------------")     #Output print
        for i in sent_packets:                          #Iterates through all of the None-elements defined above
            with open(arguments.file, "rb") as image:           #Opens the file specified by the client options
                f = image.read()[datalength:(datalength+1460)]  #Reads the next 1460 bytes from the file
                b = bytes(f)                                    #Converts the text read into bytes
                print(seqnr,".\tFrom:", datalength, "B\tTo:", datalength+1460, "B\tDifference:", (datalength+1460)-(datalength), "B\tdatalength", len(b),"B") #Output print
                if len(b) < 1460:           #Checks if the size of the read chunck is less than the maximum read-length of 1460
                    fin = 2                 #If so, this was the last bit of the file
            datalength += 1460              #Increment the datalength so that the next read-interval is the next 1460 bytes
            
            msg = create_packet(seqnr, 0, fin, arguments.windowSize, b) #Creates a packet with the current sequence number, the fin-flag (if it gets updated), the specified window size, and the data
            
            #PACKET LOSS GENERATOR
            if flag == True and arguments.test_case == "loss" and seqnr == 3:   #If the client specified that it wants to deliberatley drop a package
                flag = False                                        #Prevents the if-test to happen again after this
                print("^\tThis packet is skipped (", seqnr,")")     #Output print
            else:                                                   #If no packet loss shall happen
                clientSocket.sendto(msg, (str(arguments.serverip), arguments.port))     #Send the package with the data
            #END PACKET LOSS GENERATOR
            
            print()     #Output print (for space)
            sent_packets[windowIndex] = msg                 #Updating the list of sendt packets with the currently sendt package
            windowIndex = (seqnr)%(arguments.windowSize)    #Updating the index for the next package that will be created
            seqnr+=1                                        #Updating the sequence number    
        ###FINISH SENDING DATA
        
        ###RECIEVING ACKS
        print("RECIEVING ACKS:\n---------------") #Output print
        j = 0                           #An iterator for the next while-loop
        recieved_acks = []              #A list containing the recieved acknowledgement messages
        clientSocket.settimeout(.6)     #The client timeout has to be higher than the senders timeout

        while j < arguments.windowSize:                 #The ACK-recieving loop
            while True:                                 #Loops until break
                if arguments.test_case == "drop_ack":   #If the user deliberatley want an ACK drop
                    try:
                        message, reciever = clientSocket.recvfrom(2048)         #Checks if client can recieve anything from server
                        j+=1                                                    #If so, update the iterator
                        nothing, acknr, flags, win = parse_header(message[:12]) #Stores the ack-message
                        syn, flagack, fin = parse_flags(flags)                  #Stores the flags, in case fin == 2
                        print("Got acknr:", acknr)                              #Output print
                        if len(recieved_acks) == 0 and acknr%arguments.windowSize == 2 and arguments.test_case == "drop_ack": #Edge case if the dropped ack is the first in a window
                            print("EDGE CASE")          #Output print
                            resend_ack = create_packet(acknr,0, fin, arguments.windowSize, b'resendplz')    #Create a resend-ack-request
                            clientSocket.sendto(resend_ack, (str(arguments.serverip), arguments.port))      #Sends the request to the server
                        recieved_acks.insert((acknr-1)%arguments.windowSize, acknr)                 #Places the ack-message in the correrct place in the list
                        print("Recieved_acks", recieved_acks)       #Output print
                        break                                       #Exits the "While True:" loop
                    except timeout:                                 #If client didn't recieve an ack message
                        if arguments.test_case != "drop_ack": break #If the ACK-drop wasn't deliberate break immediatly (maybe redundant)
                        prev = 0                                    #Creates a variable for previous ACK
                        for current in recieved_acks:               #Iterates through the list of recieved ACKs
                            if current%arguments.windowSize > prev+1:   #Checks if current ACK number is more than 1 bigger than the previous ACK number
                                print("\tNB! ACK",prev+1,"lost!")           #Output print
                                print("\tSending retransmission request")   #Output print
                                resend_ack = create_packet(prev+1,0, fin, arguments.windowSize, b'resendplz')   #Create a new packet requesting a resend of ACK
                                clientSocket.sendto(resend_ack, (str(arguments.serverip), arguments.port))      #Sends this request to server
                            prev = current  #Updates the previous ACK
                else:                                   #If the loss of ACKs wasn't deliberate
                    clientSocket.settimeout(.8)         #Set the timeout of the client to be larger than the timeout of server(.7)
                    message, reciever = clientSocket.recvfrom(2048) #Recieve ACK
                    j+=1                                #Increment iterator
                    nothing, acknr, flags, win = parse_header(message[:12])     #Parse the message
                    syn, flagack, fin = parse_flags(flags)                      #Parse the flags
                    print("Got acknr:", acknr)                                  #Output print
                    recieved_acks.append(acknr)                                 #Place the recieved ack in the list
                    print("Recieved_acks", recieved_acks)                       #Output print
                    break                                                       #Break the "While: True" loop, and move on to the next number in window size
            
        print("\nGot all acks, doubles or not:\t", recieved_acks) #Output print
        
        #checking for retransmission
        ack = -1                #Variable for the ACK number of a given package
        counter = 0             #Variable for index handeling
        prevDoubleAck = 0       #Variable for previous previous ACK number
        doubleCounter = 1       #Variable for checking if double ACKs happens repeatedly
        oldack = 0              #Variable for previous ACK number
        for i in recieved_acks: #Iterates through every ACK in the list of recieved ACKs
            prevDoubleAck = oldack  #The previous previous ACK gets updated
            if prevDoubleAck == -1:prevDoubleAck = 0    #Edge case first packet gets lost
            oldack = ack                    #Updates the previous ACK
            ack = recieved_acks[counter]    #Updates the current ACK
            counter+=1                      #Updates the index handler
            if ack == oldack:               #If the current ACK is equal the previous ACK
                print("\tNB!")              #Output print
                print("\tDouble ack detected")  #Output print
                print("\tPrev ack:", oldack, "is equal current ack:",ack) #Output print
                print("\tHow often?:", prevDoubleAck) #Output print
                if prevDoubleAck == ack:            #If this coincidence happened last time as well
                    print("\tLast double ack happens again") #Output print
                    doubleCounter += 1              #Update the number of times this has happened
                    clientSocket.sendto(sent_packets[(ack+doubleCounter)%arguments.windowSize], reciever) #Sending the correct packet once again
                    print("\tResent packet nr", ack+doubleCounter)      #Output print
                    reack = clientSocket.recv(2048)                     #Listens for confirmation
                    seq, acknr, flags, win = parse_header(reack)        #Unpacks the recieved package
                    syn, flagack, fin = parse_flags(flags)              #Unpacks the flags
                    recieved_acks[counter-1] = ack                      #Updates the recieved ACK
                else:                                                   #Most common
                    clientSocket.sendto(sent_packets[ack%arguments.windowSize], reciever)   #If this double ACK didn't happen the last time, resend lost package
                    print("\tResent packet nr", ack+1)                                      #Output print
                    reack, reciever = clientSocket.recvfrom(2048)                           #Recieve ACK for recieved lost package
                    seq, acknr, flags, win = parse_header(reack[:12])                       #Unpack the header
                    recieved_acks[counter-1] = acknr                                        #Update the recieved ACKs
                    doubleCounter = 1                                                       #Resets the repeated double ack value
            elif recieved_acks[0]%arguments.windowSize== 0:         #If the first package gets dropped
                print("\tFirst packet got dropped")                 #Output print
                clientSocket.sendto(sent_packets[ack%arguments.windowSize], reciever)   #Resends first package
                reack = clientSocket.recv(2048)                     #Listens for feedback from server
                seq, acknr, flags, win = parse_header(reack[:12])   #Unpacks the header
                recieved_acks[counter-1] = acknr                    #Updates the recieved ACKs list
        print("ACKs after retransmission:\t", recieved_acks)        #Output print
        print("-----------------------------------------------------------") #Output print
        roundnr += 1 #Updates the number of rounds the loop has been through

############### FILIP END ##################

# Description
# Checks if the port number is valid
# Arguments:
#   val:        Value from the options
# Returns:      The value if valid
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

# Description
# Checks if the IP address is valid
# Arguments:
#   val:        Value from the options
# Returns:      The value if valid
def check_ip(val):                          
    try:
        val = ipaddress.ip_address(val)     #Checks with the ipaddress import if it's a valid IP
    except:
        raise argparse.ArgumentTypeError("IP-address syntax wrong") #Error-message if IP-syntax is wrong
    return val                              #If the test was OK, return the value

# Description
# Checks if the window size is valid
# Arguments:
#   val:        Value from the options
# Returns:      The value if valid
def check_windowSize(val):
    if int(val) < 5 and int(val) > 15:
        raise argparse.ArgumentTypeError("The windowsize should only be between 5 and 15")
    else:
        return int(val)

# Description
# Default server function. Finds out what reliability function to use
# Arguments
#   arguments:      List of server options
# Returns: Nothing
def server(arguments): 
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    try:
        serverSocket.bind((str(arguments.bind), arguments.port))   
    except:
        print("Bind failed - Wait and try again, or check if the IP-address is supported") 
        sys.exit()                                                                         
    
    
    while True: #an infinite loop
        data, reciever = serverSocket.recvfrom(2048)  #recieve message with pickle with client-options
        client_options = pickle.loads(data) #retrieves the client-options (unpacking)

        #Three-way-handshake
        time_out = .5
        serverSocket.settimeout(time_out)

        client_syn, clientAddress = serverSocket.recvfrom(1000)
        header_from_msg = client_syn[:12]
        seq, acknr, flags, win = parse_header(header_from_msg)
        syn, ack, fin = parse_flags(flags)
        #print("\nServer: Header information from recieved SYN package:\n\tSequence number:", seq, "\n\tAcknowledgement number:", acknr,
        #          "\n\tFlags:\n\t\tsyn:", syn, "\n\t\tack:", ack,"\n\t\tfin:", fin, "\n\tWindow size:", win)
        
        if syn > 0 and ack == 0 and fin == 0 and seq == 1 and acknr == 0:
            msg = create_packet(0, 1, 12, 0, b'')       #SYN:ACK message
            serverSocket.sendto(msg, clientAddress)
            client_ack, clientAddress = serverSocket.recvfrom(1000)
            header_from_client_ack = client_ack[:12]
            seq, acknr, flags, win = parse_header(header_from_client_ack)
            syn, ack, fin = parse_flags(flags)
            #print("Server: Header information from recieved ACK package:\n\tSequence number:", seq, "\n\tAcknowledgement number:", acknr,
            #      "\n\tFlags:\n\t\tsyn:", syn, "\n\t\tack:", ack,"\n\t\tfin:", fin, "\n\tWindow size:", win)
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
    elif client_options.reliability == "saw":
        print("The client chose Stop and wait")
        server_stop_and_wait(serverSocket, arguments, client_options)
    elif client_options.reliability == "sr":
        print("the client chose selective repeat")
        server_selective_repeat(serverSocket, arguments, client_options)

    #closing the connection gracefully
    msg = create_packet(0,0,4,0,b'')
    serverSocket.sendto(msg, reciever)
    print("\nGracefully closed the connection")
    time.sleep(1)
    serverSocket.close()

# Description
# Default client function. Finds out what reliability function to use and measures throughput
# Arguments
#   arguments:      List of server options
# Returns: Nothing
def client(arguments):
    start_time = time.time()
    
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    data_string = pickle.dumps(arguments)
    clientSocket.sendto(data_string, (str(arguments.serverip), arguments.port))

    # Three-way-handshake
    time_out = .5
    clientSocket.settimeout(time_out)
    msg = create_packet(1, 0, 8, 0, b'')  # SYN message
    clientSocket.sendto(msg, (str(arguments.serverip), arguments.port))
    while True:
        try:
            message, serverAddress = clientSocket.recvfrom(2048)  # SYN-ACK message
            header_from_msg = message[:12]
            seq, acknr, flags, win = parse_header(header_from_msg)
            syn, ack, fin = parse_flags(flags)
            #print("\nClient: Header information from recieved SYN:ACK package:\n\tSequence number:", seq, "\n\tAcknowledgement number:", acknr,
            #      "\n\tFlags:\n\t\tsyn:", syn, "\n\t\tack:", ack,"\n\t\tfin:", fin, "\n\tWindow size:", win)
            
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
    elif arguments.reliability == "saw":
            print("The client chose Stop and wait")
            client_stop_and_wait(clientSocket, arguments)
    elif arguments.reliability == "sr":
            print("the client chose selective repeat")
            client_selective_repeat(clientSocket, arguments)
    

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\nElapsed time: {elapsed_time:.3f} seconds.")
    try:
        pass
    finally:
        file_size_bytes = os.path.getsize(arguments.destination)
        print("FileSize: ", file_size_bytes)
        bytes_per_second = file_size_bytes / elapsed_time
        mBytes_per_second = bytes_per_second / 1000000
        print(f"Bytes per second: {bytes_per_second:.2f}")
        print(f"MegaBytes per second: {mBytes_per_second:.2f}")
    
    #closing the connection gracefully
    finalACK = clientSocket.recv(2048)
    syn, acknr, flags, win = parse_header(finalACK[:12])
    seq, ack, fin = parse_flags(flags)
    if ack == 4:
        print("\nGracefully closed the connection")
        clientSocket.close()
    
    
parser = argparse.ArgumentParser(description="Optional Arguments")    #Title in the -h menu over the options available

#Adds options to the program
parser.add_argument("-s", "--server", action="store_true", help="Assigns server-mode")                                          #Server specific
parser.add_argument("-c", "--client", action="store_true", help="Assigns client-mode")                                          #Client specific
parser.add_argument("-p", "--port", default="8088", type=check_port, help="Allocate a port number")                             #Server and Client specific
parser.add_argument("-I", "--serverip", type=check_ip, default="127.0.0.1", help="Set IP-address of server from client")        #Client specific
parser.add_argument("-b", "--bind", type=check_ip, default="127.0.0.1", help="Set IP-address that client can connect to")       #Server specific

parser.add_argument("-w", "--windowSize", type=check_windowSize, default=5, help="Specify window size")
parser.add_argument("-r", "--reliability", type=str, choices=("gbn", "saw", "sr"), default=None, help="Choose reliability-mode")                #Client specific
parser.add_argument("-f", "--file", type=str, default="test.txt", help="Choose file to send over")                    #Client specific
parser.add_argument("-d", "--destination", type=str, default="output.txt", help="Choose destination file")
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
