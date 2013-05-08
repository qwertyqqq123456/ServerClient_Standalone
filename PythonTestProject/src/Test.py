import socket
import threading
import SocketServer
import time

devicelist = {}

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
            if pairing_info in devicelist:
                if devicelist[pairing_info][0] == device_name:
                    devicelist[pairing_info][1] = True
                    devicelist[device_name][1] = True
                else:
                    print "Some error in devicelist: [name mismatching]"
                
            print"Current devlist:", devicelist
            response = "{0} registered" .format(device_name)
        
        elif paralist[0] == "D":
            sender_name = paralist[1]
            code = paralist[2]
            if code == "Send":
                color = paralist[3]
                brightness = paralist[4]
            
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
            
            response = "message sent to server"
                
            
        elif paralist[0] == "G":
            sender_name = paralist[1]
            if len(devicelist[sender_name]) == 3:
                response = "no message this time"
            elif len(devicelist[sender_name]) == 4:
                response = devicelist[sender_name][3]
            else:
                print "device record length error2"
        else:
            pass
            
        
        self.request.sendall(response)
        
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    'This is Threaded TCP Server'
    pass

def client(ip, port, message):
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

    client(ip, port, "R#" + "Tommy_mac#" + "Amy_windows")
    client(ip, port, "R#" + "Jeff_mac#" + "Marry_mac")
    client(ip, port, "R#" + "Amy_windows#" + "Tommy_mac")
    client(ip, port, "R#" + "Marry_mac#" + "Jeff_mac")
    client(ip, port, "R#" + "Julie_windows#" + "Frank_windows")
    client(ip, port, "R#" + "Frank_windows#" + "Julie_windows")
    
    client(ip, port, "D#" + "Tommy_mac#" + "Send#" + "Red#" + "20")
    time.sleep(1)
    client(ip, port, "G#" + "Amy_windows")
    
    time.sleep(3)
    
    client(ip, port, "D#" + "Amy_windows#" + "Reply#" + "#" + "") 
    time.sleep(1)
    client(ip, port, "G#" + "Tommy_mac")
       
    server.shutdown()
    print "Server shutdown."
    




