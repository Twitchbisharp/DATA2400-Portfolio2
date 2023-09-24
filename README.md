README-file for application.py

(This is a group project in the course DATA2400 at OsloMet -  storbyuniversitetet)

-----------------------------
HOW TO OPERATE APPLICATION.PY
-----------------------------

In order to run this program in a mininet topology, please make sure you have done the following:
1. Created a mininet topology using a python script
2. Run the topology python script from the same folder as the application.py-file
3. Opened a xterm-window on the server- and client-host.
4. Figured out the IP address of the server-host.

In order to see all options available in the program application.py, write "python3 application.py -h" in the xterm-terminal.
* The first and most important options are the -s and -c options.
    The server host shall use the -s option, while the client should use the -c option.
* The second most important option to use is the -I and -b options.
    The server shall use the -b option followed by the IP number of the server-host
    The client shall use the -I option followed by the IP number of the server-host
* If you wanted you could specify the port number of the connection, but then you have to specify this using the -p option followed by the port number on both server and client side.
* It is also vital that you specify what reliability function the client shall invoke. Specify this with the -r option followed by the acronyms of the given reliability function (stop and wait, go back n, selective repeat). Type -h for help. 
Remember that this does not need to be specified on the server side.
* When running the application with the reliability functions Go back N or Selective Repeat, you can specify the window size by invoking the -w option followed by the wanted window size.
* If you want to run the different reliability functions with test cases such as loss of packets and dropping of acks, you can write -t followed by the test case you want to use (loss, drop_ack)
* By default the input and output files are named "test.txt" and "output.txt", but you can change this by invoking the -f and -d options respectivley. Make sure to have these files already defined in the same folder as application.py


Things to remember:
* Make sure you run the server-host with the server option -s before running the client-host with the optino -c
* The client is the one who prints the throughput data.
