import argparse
import sys
import ipaddress
from socket import *
import _thread as thread
from threading import Thread
import pickle
import time
import os

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

Potential function for image extraction:
    with open("img.png", "rb") as image:
      f = image.read()
      b = bytearray(f)
      print b[0]

    # Convert image to bytes
    import PIL.Image as Image
    pil_im = Image.fromarray(image)
    b = io.BytesIO()
    pil_im.save(b, 'jpeg')
    im_bytes = b.getvalue()

    
    import base64
    with open("t.png", "rb") as imageFile:
        str = base64.b64encode(imageFile.read())
        print str
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

def server_stop_and_wait(serverSocket, arguments):
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

################### WILLIAM START ###################
#SERVER
def server_go_back_n(serverSocket, arguments, client_options):
    print("Server Go-Back-N")
    print("New window count: 1")

    window_size = client_options.windowSize
    fin = 0
    allMessages = []
    seqnr = 0
    new_window = 1

    while fin != 2:
        print("New window of " + str(window_size) + " packets created")
        window_messages = [None] * window_size

        for i in range(window_size):
            try:
                msg, reciever = serverSocket.recvfrom(2048)
            except timeout:
                print("timeout")
                break

            seq, ack, flags, win = parse_header(msg[:12])
            syn, ackflag, fin = parse_flags(flags)

            #ACK DROP
            if seq == 2:
                print("\n\nDropped ACK packet for nr 2")
                continue
                     
            window_messages[i] = msg 
            seqnr += 1

        print("Sending ACK for packet with seq " + str(seq))
        ackpkt = create_packet(0, seq, 0, window_size, b'')
        serverSocket.sendto(ackpkt, reciever)
        
        allMessages.extend(window_messages)
        print("Finished sending ACK\n")
        print("Flags:", flags, "\nSyn:", syn, "Ack", ackflag, "Fin", fin)
        new_window +=1
        print("New window count: ", str(new_window))

    datalist = []
    for i in allMessages:
        if i == None:
            continue
        else:
            data = i[12:]
            datalist.append(data)
    with open(arguments.destination, 'w') as f:   
        for i in datalist:
            f.write(str(repr(i)[2:-1])) 
### CLIENT ----------------------
def client_go_back_n(clientSocket, arguments):
    print("Client Go-Back-N")
    print("New window count: 1")

    fin = 0
    next_seqnum = 1
    datalength = 0
    sent_packets = []
    seq = 0
    int(seq)
    new_window = 1

    while fin != 2:
        print("\nFIN ==", fin)
        #sent_packets = []
        windowIndex = 1
        
        #sending data
        for i in range(arguments.windowSize):
            with open(arguments.file, "rb") as name:
                f = name.read()[datalength:(datalength+1460)]
                b = bytes(f)
                print("From:", datalength, "To:", datalength+1460, "Difference:", len(b), "b sin length", len(b))
                if len(b) < 1460:
                    fin = 2
            datalength += 1460
            msg = create_packet(next_seqnum, 0, fin, arguments.windowSize, b)

            clientSocket.sendto(msg, (str(arguments.serverip), arguments.port)) 
            print("Sent packet nr:", next_seqnum, "with window-index.", windowIndex, "\n")
            sent_packets.append(msg)
            next_seqnum += 1
            windowIndex += 1
            seq += 1    

        try:
            recpkt, reciever = clientSocket.recvfrom(2048)
            xxxyyy, acknr, flags, win = parse_header(recpkt)

            print("Recieved ACK for packet with seq " + str(seq))
        except timeout:
            print("timeout, resending window")
            continue

        while acknr < next_seqnum and len(sent_packets) > 0:
            acknr += 1
            sent_packets.pop(0)
        
        new_window += 1
        print("New window count: ", str(new_window))
    print("Finished sending packets\n")
################# WILLIAM SLUTT ###################

################# FILIP START ##################      
def server_selective_repeat(serverSocket, arguments, client_options):
    print("Server Selective Repeat")
    
    window_size = client_options.windowSize
    fin = 0
    allMessages = []
    seq = 0
    seqnr = 0
    reciever = (None, None)
    squeuer = 0
    while fin != 2:
        print("New window of 5 packets created")
        window_messages = [None] * window_size
        
        while True:
        #for i in range(window_size):
            print("seq", seq, "seqnr", seqnr)
            if seq >= seqnr:
                oldseq = seq
            elif seqnr > seq:
                oldseq = seqnr
            #
            try:
                serverSocket.settimeout(.7)
                msg, reciever = serverSocket.recvfrom(2048)
            except timeout:
                #print("timeout skal ødelegge")
                break
            seq, ack, flags, win = parse_header(msg[:12])
            syn, ackflag, fin = parse_flags(flags)
            diff = seq - oldseq
            print("oldseq:", oldseq, "\tseq:", seq, "\tdiff:",diff, "\n")

            if diff == 1:     #if this is true, the packet came in sequence
                #print("seq", seq, "windowSize", arguments.windowSize)
                #print("plassering", ((seq-1)%arguments.windowSize))
                window_messages[((seq-1)%arguments.windowSize)] = msg              #places msg in correct window_messages-list, indexing makes it seq-1
                #print("windowMessages",window_messages)
            else:           #packet came out of order/lost
                #print("oldseq", oldseq, "seq", seq, "plassering:", (oldseq%arguments.windowSize)+diff-1)
                window_messages[(oldseq%arguments.windowSize)+diff-1] = msg
            #print(window_messages[:12])
        #allMessages.extend(window_messages)
        #print(allMessages)
        
        #ACK sending
        print("ACK sending")
        j=1
        errors = -1
        ack_loss_flag = True
        
        while errors != 0:
            #print("errors", errors)
            #ERROR RETRANSMISSION LOOP
            #itererer gjennom antall error
            for i in range(errors):
                print("errors left:", errors)
                #får pakke på nytt fra checking for retransmission
                retransmit, reciever = serverSocket.recvfrom(2048)          
                #henter ut seqnr
                seqnr, ack, flags, win = parse_header(retransmit[:12])      
                syn, ackflag, fin = parse_flags(flags)
                print("Recieved retransmit seq:", seqnr)
                
                #oppdsaterer window-messages til å ha riktig package
                window_messages[(seqnr%arguments.windowSize)-1] = retransmit                             #setter msg på riktig plass i allMessages, må bruke seq-1 for indexering
                #print(retransmit)
                
                #lager en ack for oppdatert package
                reack = create_packet(0,seqnr,fin,window_size, b'reack')
                serverSocket.sendto(reack, reciever)
                errors-=1
            errors = 0
            #END ERROR RETRANSMISSION LOOP

            flag = True
            #while j%(window_size+1) != 0:           #itererer gjennom alle meldinger for å sjekke om de eksisterer
            for i in range(client_options.windowSize):
                #print("windowMessages[0]", window_messages[0])
                if window_messages[i] == None:    #if packet isn't recieved       
                    #retransmit call
                    retransmit = create_packet(0,seqnr,0,window_size,b'')
                    serverSocket.sendto(retransmit, reciever)
                    print("sent error:", i+1)
                    #går inn i ERROR retransmission loop når vi har gått gjennom alle window_messages
                    errors +=1
                else:                   #Har fått package - sending regular ack
                    seq, ack, flags, win = parse_header(window_messages[i][:12]) #finds current seqnr
                    syn, ackflag, fin = parse_flags(flags)  #oppdatering av fin
                    
                    #Lager ack-header
                    msg = create_packet(0,seq, fin, client_options.windowSize, b'')
                    
                    #DROP_ACK GENERATOR
                    if flag == True and client_options.test_case == "drop_ack" and seq == 3:
                        flag = False
                        print("Skipped ack:", seq)

                    else:
                        #Sending packet
                        serverSocket.sendto(msg, reciever) 
                        print("sent:", seq)
                        
              
        squeuer+=1
        allMessages.extend(window_messages)
        #print(window_messages)
        print("finished sending acks\n")
        print("flags:", flags, "\n\tsyn:", syn, "ack", ackflag,"fin", fin)
    datalist = []
    for i in allMessages:
        data = i[12:]
        datalist.append(data)
    with open(client_options.destination, 'w') as f:   
        for i in datalist:
            f.write(str(repr(i)[2:-1]))
    
    

def client_selective_repeat(clientSocket, arguments):
    print("Client Selective Repeat")
    fin = 0
    roundnr = 1
    datalength = 0
    seqnr = 1
    flag = True
    squeuer = 0
    while fin != 2:
        print("\nFIN ==", fin)
        sent_packets = [None] * 5
        windowIndex = (seqnr-1)%(arguments.windowSize)
        
        ####----------START SENDING DATA
        #itererer gjennom listen sent_packets
        for i in sent_packets:
            #reads the specified file
            with open(arguments.file, "rb") as image:
                f = image.read()[datalength:(datalength+1460)]
                b = bytes(f)
                print("From:", datalength, "To:", datalength+1460, "Difference:", (datalength+1460)-(datalength), "b sin length", len(b))
                if len(b) < 1460:
                    fin = 2
            datalength += 1460
            
            #create a message
            msg = create_packet(seqnr, 0, fin, arguments.windowSize, b)
            
            #PACKET LOSS GENERATOR
            if flag == True and arguments.test_case == "loss" and seqnr == 9:
                flag = False
                print("Skipped packet:", seqnr, "\n")
            else:
                clientSocket.sendto(msg, (str(arguments.serverip), arguments.port)) 
                print("sent packet nr:", seqnr, "with window-index.", windowIndex, "\n")
            #END PACKET LOSS GENERATOR
            
            #oppdaterer sent_packets-lista
            sent_packets[windowIndex] = msg
            #oppdaterer windowIndex
            windowIndex = (seqnr)%(arguments.windowSize)
            #oppdaterer seqence number
            seqnr+=1
            
        #print(sent_packets)
        ###-----------FINISH SENDING DATA
        
        #Recieving acks
        j = 0
        recieved_acks = []
        clientSocket.settimeout(.6)
        ack = 1
        while j < 5:     #ack_recieving loop
            while True:
                try:
                    message, reciever = clientSocket.recvfrom(2048)
                    break
                except timeout:
                    resend_ack = create_packet(ack-1,0, fin, arguments.windowSize, b'resendplz')
                    #clientSocket.sendto(resend_ack, reciever)
                    #print("sendt resend ack request", ack-1)
            seq, ack, flags, win = parse_header(message[:12])
            syn, flagack, fin = parse_flags(flags)
            print("got acknr:", ack) 
            j+=1
            recieved_acks.append(ack)
            print("Recieved_acks", recieved_acks)
            

            
        #prints all acks
        print("Got all acks, doubles or not", recieved_acks)
        
        #checking for retransmission
        ack = -1
        counter = 0
        prevDoubleAck = 0
        doubleCounter = 1
        oldack = 0
        for i in recieved_acks:
            print("i:", i)
            prevDoubleAck = oldack
            if prevDoubleAck == -1:prevDoubleAck = 0    #edge case first packet lost
            oldack = ack
            ack = recieved_acks[counter]
            counter+=1
            if ack == oldack:
                print("dobbel ack")
                print("oldack:", oldack, "is equal",ack)
                print("prevDoubleAck:", prevDoubleAck)
                if prevDoubleAck == ack:
                    print("forrige double skjer igjen")
                    doubleCounter += 1
                    sent_packets[ack%arguments.windowSize] = create_packet(ack+doubleCounter, 0, fin, 0,b'retransmitted')
                    clientSocket.sendto(sent_packets[ack%arguments.windowSize], reciever)
                    print("Resent packet with index", ack, "i.e. ack", ack+doubleCounter)
                    reack = clientSocket.recv(2048)
                    seq, acknr, flags, win = parse_header(reack)
                    syn, flagack, fin = parse_flags(flags)
                    recieved_acks[counter-1] = ack
                else:   #vanligst
                    sent_packets[ack%arguments.windowSize] = create_packet(ack+1, 0, fin, 0, b'retransmitted')
                    clientSocket.sendto(sent_packets[ack%arguments.windowSize], reciever)
                    print("resent packet with index", ack, "i.e. ack", ack+1)
                    reack = clientSocket.recv(2048)
                    seq, acknr, flags, win = parse_header(reack)
                    recieved_acks[counter-1] = acknr
                    doubleCounter = 1       # må resette denne når andre acknr blir doble
            elif recieved_acks[0]%arguments.windowSize== 0:
                print("first packet got dropped")
                #print("The packet:", sent_packets[ack%arguments.windowSize])
                sent_packets[ack%arguments.windowSize] = create_packet(ack+1, 0, fin, 0, b'retransmitted')
                clientSocket.sendto(sent_packets[ack%arguments.windowSize], reciever)
                reack = clientSocket.recv(2048)
                seq, acknr, flags, win = parse_header(reack)
                recieved_acks[counter-1] = acknr
        print("recieved_acks:", recieved_acks)
        roundnr += 1
        
        #fin += 1
        
    
        ##TODO: 
        # implementere resend på timeout
        # implementere tester for forsikrer retransmission (sendloss og ackloss)    
        # oppdatere ok-løkke til å være kompatibel med ulike windowSizes
############### FILIP SLUTT ##################

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

def check_windowSize(val):
    if val < 5 and val > 15:
        raise argparse.ArgumentTypeError("The windowsize should only be between 5 and 15")
    else:
        return int(val)

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
    print(f"Elapsed time: {elapsed_time:.3f} seconds.")
    try:
        pass
    finally:
        with open('output.txt', 'rb') as output_file:
            byte_string = output_file.read()
        file_size_bytes = os.path.getsize('output.txt')
        print("FileSize: ", file_size_bytes)
        bytes_per_second = file_size_bytes / elapsed_time
        mBytes_per_second = bytes_per_second / 1000000
        print(f"Bytes per second: {bytes_per_second:.2f}")
        print(f"MegaBytes per second: {mBytes_per_second:.2f}")

     
    
    
parser = argparse.ArgumentParser(description="Optional Arguments")    #Title in the -h menu over the options available

#Adds options to the program
parser.add_argument("-s", "--server", action="store_true", help="Assigns server-mode")                                          #Server specific
parser.add_argument("-c", "--client", action="store_true", help="Assigns client-mode")                                          #Client specific
parser.add_argument("-p", "--port", default="8088", type=check_port, help="Allocate a port number")                             #Server and Client specific
parser.add_argument("-I", "--serverip", type=check_ip, default="127.0.0.1", help="Set IP-address of server from client")        #Client specific
parser.add_argument("-b", "--bind", type=check_ip, default="127.0.0.1", help="Set IP-address that client can connect to")       #Server specific

parser.add_argument("-w", "--windowSize", type=check_windowSize, default=5, help="Specify window size")
parser.add_argument("-r", "--reliability", type=str, choices=("gbn", "saw", "sr"), default=None, help="Choose reliability-mode")                #Client specific
parser.add_argument("-f", "--file", type=check_file, default="test.txt", help="Choose file to send over")                    #Client specific
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
