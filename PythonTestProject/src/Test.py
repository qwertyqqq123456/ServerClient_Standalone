import socket
import threading
import SocketServer
import time
import Queue
from random import randrange


devlist_pairinfo = 0
devlist_connected = 1
devlist_isalive = 2
devlist_timer = 3
devlist_lock = 4
devlist_queue = 5

TTL = 40.0

devicelist = {}
devicenumber_index = {}
indexlock = threading.Lock()

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
            
            if device_name not in devicelist:
                devicelist[device_name] = [pairing_info, connected, isalive, threading.Timer(TTL, client_die, args=[device_name]), threading.Lock()]
                
                try:
                    devicelist[device_name][devlist_timer].start() 
                except RuntimeError as e:
                    print str(e)
                
                indexlock.acquire()
                devicenumber = len(devicenumber_index) + 1
                devicenumber_index[devicenumber] = device_name
                indexlock.release()
                
                if pairing_info in devicelist:
                    if devicelist[pairing_info][devlist_pairinfo] == device_name:
                        
                        devicelist[pairing_info][devlist_lock].acquire()
                        devicelist[pairing_info][devlist_connected] = True
                        devicelist[pairing_info].append(Queue.Queue(5))
                        devicelist[pairing_info][devlist_lock].release()
                        
                        devicelist[device_name][devlist_lock].acquire()
                        devicelist[device_name][devlist_connected] = True
                        devicelist[device_name].append(Queue.Queue(5))
                        devicelist[device_name][devlist_lock].release()
                        
                    else:
                        print "Some error in devicelist: [name mismatching]"
                    
                # print"Current devlist:", devicelist
                # print"Current devicenumber_index:", devicenumber_index
                response = "{0} registered as {1}" .format(device_name, devicenumber)
            else:
                response = "{0} has already been registered.".format(device_name)
        
        elif paralist[0] == "D":
            sender_number = int(paralist[1])
            code = paralist[2]             
            if code == "Send":
                color = paralist[3]
                brightness = paralist[4]
                         
            if sender_number in devicenumber_index:
                sender_name = devicenumber_index[sender_number]

                if sender_name in devicelist:
                    
                    handle_alivesignal(sender_name)
                    
                    'Response'    
                    try:
                        response = devicelist[sender_name][devlist_queue].get(False)
                        devicelist[sender_name][devlist_queue].task_done()
                    except Queue.Empty:
                        response = "No message this time"
                                
                    response = sender_name + ": " + response
                    
                    if devicelist[sender_name][devlist_pairinfo] in devicelist:
                    
                        if devicelist[sender_name][devlist_connected] == True \
                        and devicelist[devicelist[sender_name][devlist_pairinfo]][devlist_connected] == True:
                        
                            'Send msg'
                            if code == "Send":
                                operation = "Send " + color + " " + brightness
                            elif code == "Reply":
                                operation = "Reply"
                            else:
                                print "error code"                                                          
                            # print"operation:", operation
                            
                            try:
                                devicelist[devicelist[sender_name][devlist_pairinfo]][devlist_queue].put(operation, False)
                            except Queue.Full:
                                print "The queue is full, try again later"
                                
                        else:
                            response += "\nWarning: This device is not connected."
                    else:
                        response += "\nWarning: The pair information is not recorded."
                else:
                    response = "Error: This email appears in index list but not the devicelist."               
            else:
                response = "Error: Didn't find this device number in system!"
        elif paralist[0] == "N":
            sender_number = int(paralist[1])
            if sender_number in devicenumber_index:
                sender_name = devicenumber_index[sender_number]

                if sender_name in devicelist:                  
                    handle_alivesignal(sender_name)
                    
                    'Response'    
                    try:
                        response = devicelist[sender_name][devlist_queue].get(False)
                        devicelist[sender_name][devlist_queue].task_done()
                    except Queue.Empty:
                        response = "No message this time"
                                
                    response = sender_name + ": " + response                   
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

def handle_alivesignal(devicename):
    'This function handles the alive signal sent by clients.'
    
    devicelist[devicename][devlist_lock].acquire()
    if devicelist[devicename][devlist_isalive] == True:
        devicelist[devicename][devlist_timer].cancel()
        devicelist[devicename][devlist_timer] = threading.Timer(TTL, client_die, args=[devicename])        
        devicelist[devicename][devlist_timer].start()        
    else:
        devicelist[devicename][devlist_isalive] = True
        if devicelist[devicename][devlist_pairinfo] in devicelist:
            if devicelist[devicelist[devicename][devlist_pairinfo]][devlist_isalive] == True:
                devicelist[devicename][devlist_connected] = True
                devicelist[devicelist[devicename][devlist_pairinfo]][devlist_connected] = True
            else:
                print "Cannot reconnect: the pair device is dead."
        else:
            print "Cannot reconnect: the pair info is not recorded."
    devicelist[devicename][devlist_lock].release()

def client_die(devicename):
    'Performing operations when the server thinks this device is dead'
    
    devicelist[devicename][devlist_lock].acquire()   
    if devicelist[devicename][devlist_pairinfo] in devicelist:
        devicelist[devicename][devlist_connected] = False
        devicelist[devicelist[devicename][devlist_pairinfo]][devlist_connected] = False
        try:
            devicelist[devicename][devlist_queue].clear()
            devicelist[devicelist[devicename][devlist_pairinfo]][devlist_queue].clear()
        except Queue.Empty:
            print "This queue is already empty, no need to clear."
    else:
        print "Warning: missing the pair information, cannot make it disconnected, die alone"
    devicelist[devicename][devlist_isalive] = False
    devicelist[devicename][devlist_lock].release()
    # May include another timer to indicate when to clear the long-dead device record

def client(ip, port, message):
    randtime = randrange(0, 15)
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
    
    HOST, PORT = "localhost", 36666
    
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address
    print "ip,port= ", ip, port
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print "Loop...server thread name: ", server_thread.name
    print "\n"

    totalnumber = 5000
    times = 4000
    
    for i in range(1, (totalnumber / 2) + 1):
        reg_message = "R#Client{0}#Client{1}".format(i, (i + totalnumber / 2))
        (threading.Thread(target=client, args=(ip, port, reg_message))).start()
    for i in range((totalnumber / 2) + 1, totalnumber + 1):
        reg_message = "R#Client{0}#Client{1}".format(i, (i - totalnumber / 2))
        (threading.Thread(target=client, args=(ip, port, reg_message))).start()

    print "Waiting for registration to be completed...\n"
    time.sleep(40)
    
    for j in range(times):
        randnumber_1 = randrange(1, totalnumber + 101)
        randnumber_2 = randrange(1, totalnumber)
        if randnumber_1 % 2 == 0:
            msg = "D#{0}#Send#Red#20".format(randnumber_2) 
        else:
            msg = "D#{0}#Reply##".format(randnumber_2)
        
        (threading.Thread(target=client, args=(ip, port, msg))).start()
    
    time.sleep(80)   
    server.shutdown()
    print "Server shutdown." 

"""import sys
import struct

result = struct.pack('!h', 77)
print result + "|" + str(sys.getsizeof(result))


dic = {}    
for n in range(60000):
    dic[str(n) * 6] = range(110)
print sys.getsizeof(dic)"""
    




