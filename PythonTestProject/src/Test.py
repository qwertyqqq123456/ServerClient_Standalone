import socket
import threading
import SocketServer
import time
from random import randrange

devicelist = {}
devicenumber_index = {}

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    'This handler is for handling request on server'
    def handle(self):
        'This function handles the processing of the requests'
        data = self.request.recv(128)
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
                if devicelist[pairing_info][0] == device_name:
                    devicelist[pairing_info][1] = True
                    devicelist[device_name][1] = True
                else:
                    print "Some error in devicelist: [name mismatching]"
                
            print"Current devlist:", devicelist
            print"Current devicenumber_index:", devicenumber_index
            response = "{0} registered as {1}" .format(device_name, devicenumber)
        
        elif paralist[0] == "D":
            sender_number = int(paralist[1])
            code = paralist[2]             
            if code == "Send":
                color = paralist[3]
                brightness = paralist[4]
                         
            if sender_number in devicenumber_index:
                sender_name = devicenumber_index[sender_number]

                'Send msg'
                if code == "Send":
                    operation = "Send " + color + " " + brightness
                elif code == "Reply":
                    operation = "Reply"
                else:
                    print "error code"
                    
                if len(devicelist[devicelist[sender_name][0]]) == 3:
                    devicelist[devicelist[sender_name][0]].append(operation)
                elif len(devicelist[devicelist[sender_name][0]]) == 4:
                    devicelist[devicelist[sender_name][0]][3] = operation
                else:
                    print "device record length error"
                
                'Response'    
                if len(devicelist[sender_name]) == 3:
                    response = "no message this time"
                elif len(devicelist[sender_name]) == 4:
                    response = devicelist[sender_name][3]
                else:
                    print "device record length error2"
                response = sender_name + ": " + response
                
            else:
                response = "Didn't find this device number in system!"
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
        response = sock.recv(128)
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

    totalnumber = 10
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
       
    """erver.shutdown()
    print "Server shutdown." """
    




