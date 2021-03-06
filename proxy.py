#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTTP Proxy Server in Python

"""
import socket
import threading
import thread
import select
import signal
import sys
import time
import argparse
import logging

BUFLEN = 4096 * 4
TIMEOUT = 60
PASS = ''
RESPONSE = 'HTTP/1.1 200 <font color="blue">By: Joe Linux</font> \r\nContent-length: 100\r\n\r\n'

def with_color(c, s):
    return "\x1b[%dm%s\x1b[0m" % (c, s)

logger = logging.getLogger(__name__)

class Server(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.running = False
        self.host = host
        self.port = port
        self.threads = []

    def run(self):
        self.soc = socket.socket(socket.AF_INET)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soc.settimeout(2)
        self.soc.bind((self.host, self.port))
        self.soc.listen(0)
        self.running = True
            
        while self.running:
            try:
                c, addr = self.soc.accept()
                c.setblocking(1)
                print 'Connection:', addr,
            except socket.timeout:
                continue
            
            conn = ConnectionHandler(c, self.threads)
            self.threads.append(conn)
            conn.start();
                
    def close(self):
        try:
            self.soc.close() 
            for c in self.threads:
                c.close()
        finally:
            self.running = False
        

class ConnectionHandler(threading.Thread):
    def __init__(self, socClient, threadsList):
        threading.Thread.__init__(self)
        self.clientClosed = False
        self.targetClosed = True
        self.client = socClient
        self.client_buffer = ''
        self.threadsPool = threadsList

    def close(self):
        self.threadsPool.remove(self)
        try:
            if not self.clientClosed:
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
                self.clientClosed = True
        except:
            print '',
        finally:
            try:
                if not self.targetClosed:
                    self.target.shutdown(socket.SHUT_RDWR)
                    self.target.close()
                    self.targetClosed = True
            except:
            	print '', 

    def run(self):
        try:
            self.client_buffer = self.client.recv(BUFLEN)
        
            hostPort = self.findHeader(self.client_buffer, 'X-Real-Host')

            if hostPort == '':
                hostPort = 'localhost:443'

            split = self.findHeader(self.client_buffer, 'X-Split')

            if split != '':
                self.client.recv(BUFLEN)
            
            if hostPort != '':
                passwd = self.findHeader(self.client_buffer, 'X-Pass')
                
                if len(PASS) == 0 or passwd == PASS:
                    #if hostPort.find('127.0.0.1') != -1:
                        #self.method_CONNECT(hostPort)

                    self.method_CONNECT(hostPort)
                else:
                    print '- Wrong pass!'
                    self.client.send('HTTP/1.1 400 WrongPass!\r\n\r\n')
            else:
                print '- No X-Real-Host!'
                self.client.send('HTTP/1.1 400 NoXRealHost!\r\n\r\n')

        #except:
            #print '- Error!'
        finally:
            self.close()

    def findHeader(self, head, header):
        aux = head.find(header + ': ')
    
        if aux == -1:
            return ''

        aux = head.find(':', aux)
        head = head[aux+2:]
        aux = head.find('\r\n')

        if aux == -1:
            return ''

        return head[:aux];

    def connect_target(self, host):
        i = host.find(':')
        if i != -1:
            port = int(host[i+1:])
            host = host[:i]
        else:
            if self.method=='CONNECT':
                port = 443
            else:
                port = 80

        (soc_family, soc_type, proto, _, address) = socket.getaddrinfo(host, port)[0]

        self.target = socket.socket(soc_family, soc_type, proto)
        self.targetClosed = False
        self.target.connect(address)

    def method_CONNECT(self, path):
        print '- CONNECT ' + path
        
        self.connect_target(path)
        self.client.send(RESPONSE)
        self.client_buffer = ''

        self.doCONNECT()

    def doCONNECT(self):
        socs = [self.client, self.target]
        count = 0
        error = False
        while True:
            count += 1
            (recv, _, err) = select.select(socs, [], socs, 3)
            if err:
                error = True
            if recv:
                for in_ in recv:
		    try:
                        data = in_.recv(BUFLEN)
                        if data:
			    if in_ is self.target:
				self.client.send(data)
                            else:
                                while data:
                                    byte = self.target.send(data)
                                    data = data[byte:]

                            count = 0
			else:
			    break
		    except:
                        error = True
                        break
            if count == TIMEOUT:
                error = True

            if error:
                break

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--host', default='127.0.0.1', help='Padrão: 127.0.0.1')
    parser.add_argument('--port', default='80', help='Padrão: 80')
    args = parser.parse_args()
    
    host = args.host
    port = int(args.port)
   
    print with_color (32, "Proxy HTTP funcionando corretamente")
    print with_color (32, "IP do Servidor:") + host
    print with_color (32, "Porta:") + str(port)
    
    server = Server(host, port)
    server.start()
                            
    while True:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print with_color (32, "\nSaindo...")
            server.close()
            break
    
if __name__ == '__main__':
    main()
