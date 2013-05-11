import socket
import threading
import SocketServer
import time
import Queue
import sys
from random import randrange


devlist_pairinfo = 0
devlist_connected = 1
devlist_isalive = 2
devlist_queue = 3

devicelist = {}
devicenumber_index = {}

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    'This handler is for handling request on server'
    def handle(self):
        'This function handles the processing of the requests'
        data = self.request.recv(1024)
        paralist = data.split("#")
        
        if paralist[0] == "R":          
            device_name = paralist[1]
            pairing_info = paralist[2]
            connected = False
            isalive = True
            devicelist[device_name] = [pairing_info, connected, isalive]
            
            devicenumber = len(devicenumber_index) + 1
            devicenumber_index[devicenumber] = device_name
            
            if pairing_info in devicelist:
                if devicelist[pairing_info][devlist_pairinfo] == device_name:
                    devicelist[pairing_info][devlist_connected] = True
                    devicelist[device_name][devlist_connected] = True
                    devicelist[pairing_info].append(Queue.Queue(5))
                    devicelist[device_name].append(Queue.Queue(5))
                else:
                    print "Some error in devicelist: [name mismatching]"
                
            # print"Current devlist:", devicelist
            # print"Current devicenumber_index:", devicenumber_index
            response = "{0} registered as {1}" .format(device_name, devicenumber)
        
        elif paralist[0] == "D":
            sender_number = int(paralist[1])
            code = paralist[2]             
            if code == "Send":
                color = paralist[3]
                brightness = paralist[4]
                         
            if sender_number in devicenumber_index:
                sender_name = devicenumber_index[sender_number]

                if sender_name in devicelist:
                    if devicelist[sender_name][devlist_connected] == True \
                    and devicelist[devicelist[sender_name][devlist_pairinfo]][devlist_connected] == True:
                    
                        'Send msg'
                        if code == "Send":
                            operation = "Send " + color + " " + brightness
                        elif code == "Reply":
                            operation = "Reply"
                        else:
                            print "error code"
                            
                        """if len(devicelist[devicelist[sender_name][devlist_pairinfo]]) == 3:
                            devicelist[devicelist[sender_name][devlist_pairinfo]].append(operation)
                        elif len(devicelist[devicelist[sender_name][devlist_pairinfo]]) == 4:
                            devicelist[devicelist[sender_name][devlist_pairinfo]][3] = operation
                        else:
                            print "device record length error" """
                        
                        # print"operation:", operation
                        
                        try:
                            devicelist[devicelist[sender_name][devlist_pairinfo]][devlist_queue].put(operation)
                        except Queue.Full:
                            print "The queue is full, try again later"
                            
                        'Response'    
                        """if len(devicelist[sender_name]) == 3:
                            response = "no message this time"
                        elif len(devicelist[sender_name]) == 4:
                            response = devicelist[sender_name][3]
                        else:
                            print "device record length error2" """
                        if devicelist[sender_name][devlist_queue].empty():
                            response = "queue is empty"
                        else:
                            response = devicelist[sender_name][devlist_queue].get()
                            devicelist[sender_name][devlist_queue].task_done()
                            
                        response = sender_name + ": " + response
                    else:
                        response = "Error: This device is not connected."
                else:
                    response = "Error: This email appears in index list but not the devicelist."               
            else:
                response = "Error: Didn't find this device number in system!"
        else:
            pass          
        
        self.request.sendall(response)
        
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    'This is Threaded TCP Server'
    pass

def client(ip, port, message):
    randtime = randrange(0, 7)
    time.sleep(randtime)
    'This function is for executing client logic'
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        sock.sendall(message)
        response = sock.recv(1024)
        print"Received: {}".format(response)
    finally:
        sock.close()

if __name__ == "__main__":
    
    HOST, PORT = "localhost", 0
    
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address
    print "ip,port= ", ip, port
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print "Loop...server thread name: ", server_thread.name
    print "\n"

    totalnumber = 100
    times = 20
    
    for i in range(1, (totalnumber / 2) + 1):
        reg_message = "R#Client{0}#Client{1}".format(i, (i + totalnumber / 2))
        (threading.Thread(target=client, args=(ip, port, reg_message))).start()
    for i in range((totalnumber / 2) + 1, totalnumber + 1):
        reg_message = "R#Client{0}#Client{1}".format(i, (i - totalnumber / 2))
        (threading.Thread(target=client, args=(ip, port, reg_message))).start()

    print "Waiting for registration to be completed...\n"
    time.sleep(30)
    
    for j in range(times):
        randnumber_1 = randrange(1, totalnumber + 101)
        randnumber_2 = randrange(1, totalnumber)
        if randnumber_1 % 2 == 0:
            msg = "D#{0}#Send#Red#20".format(randnumber_2) 
        else:
            msg = "D#{0}#Reply##".format(randnumber_2)
        
        (threading.Thread(target=client, args=(ip, port, msg))).start()
    
    time.sleep(30)   
    server.shutdown()
    print "Server shutdown." 

"""import sys

dic = {}    
for n in range(60000):
    dic[str(n) * 6] = range(110)
print sys.getsizeof(dic)"""
    




