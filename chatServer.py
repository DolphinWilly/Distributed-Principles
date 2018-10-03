#!/usr/bin/env python

import os
import select
import signal
import subprocess
import sys
import time
from socket import SOCK_STREAM, socket, AF_INET,SOL_SOCKET, SO_REUSEADDR
from threading import Thread
from thread import *

## needs this server id, num of servers, and port to connect the master
if len(sys.argv) != 4:
    print "invalid args to start this chatServer"
    exit ()

address = 'localhost'
this_id = int(sys.argv[1])
num = int(sys.argv[2])
port = int(sys.argv[3])

# we already knew the port to connect to the master
master_soc = socket(AF_INET, SOCK_STREAM)
master_soc.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
master_soc.bind((address,port))
master_soc.listen(1)

# 20000 + id is the port to connect this server from others
this_soc = socket(AF_INET, SOCK_STREAM)
this_soc.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
this_soc.bind((address,20000 + this_id))
this_soc.listen(num)   # what argument to put in here

##
###### global
list_of_clients = [] # id list
log = [] # list of string as message logs from other servers
connect_list = [] # modified in sendHandler

class ClientHandlerM(Thread):
    def __init__(self, conn, address):
        Thread.__init__(self)
        self.conn = conn
        self.address = address
        # all message received from other servers
        self.buffer = ""

    def run(self):
        global list_of_clients,connect_list,log
        while True:
            data = self.conn.recv(1024)
            if data == '': # master is down?
                self.conn.close()
                exit() ### should we exit here?
                break
            else: # we actually get something from the master
                self.buffer += data
            ## now let's see our buffer
            while True:
                buffer_list = self.buffer.split("\n",1)
                if(len(buffer_list) <= 1):
                    break # we haven't receive the whole message
                else:
                    cmd = buffer_list[0]
                    self.buffer = self.buffer[len(cmd)+1:] # get the rest of the message
                    if cmd == 'get':
                        str_ = 'messages '
                        str_len = 8
                        for m in log:
                            str_len = str_len + len(m) + 1
                            str_ = str_ + m +','
                        if str_len > 8:
                            str_ = str(str_len)+'-'+str_[:len(str_)-1]
                        else:
                            str_ = '9-messages '
                        self.conn.sendall(str_)
                    elif cmd == 'alive':
                        str_ = 'alive '
                        str_len = 5
                        # sort list_of_clients
                        l = [id for id in list_of_clients]
                        #list_of_clients.sort()
                        l.append(this_id)
                        l.sort()
                        for i in l:
                            str_len = str_len + len(str(i)) + 1
                            str_ = str_ + str(i) + ','
                        if str_len > 5:
                            str_ = str(str_len)+'-'+str_[:len(str_)-1]
                        else:
                            str_ = '6-alive '
                        self.conn.sendall(str_)
                    else: # cmd is broadcasting a message
                        message = cmd.split(None,1)[1]
                        log.append(message)
                        for clients in connect_list:
                            try:
                                clients.sendall(message + "\n") ## to separate messages??
                            except:
                                clients.close()
                                connect_list.remove(clients) # you sure?

class ClientHandlerS(Thread):
    def __init__(self, conn, address):
        Thread.__init__(self)
        self.conn = conn
        self.address = address
        # all message received from other servers
        self.buffer = ""
    def run(self):
        global log
        while True:
            data = self.conn.recv(1024)
            if data == '': # the other server is down
                self.conn.close()
                if self.conn in connect_list:
                    connect_list.remove(self.conn) # should we remove ??
                break
            else: # we actually get something from the master
                data = data.replace('-', '')
                self.buffer += data
            ## now let's see our buffer

                while True:
                    buffer_list = self.buffer.split("\n",1)
                    if(len(buffer_list) <= 1):
                        break # we haven't receive the whole message
                    message = buffer_list[0]
                    self.buffer = self.buffer[len(message)+1:] # get the rest of the message
                    log.append(message)


class SendHandler(Thread):
    def __init__(self, id, address):
        Thread.__init__(self)
        self.id = id
        self.address = address

    def run(self):
        global list_of_clients, connect_list
        sock = socket(AF_INET, SOCK_STREAM)
        while True:
            time.sleep(0.4)
            try:
                if not sock in connect_list:
                    sock.connect((self.address,20000+self.id))
                    connect_list.append(sock)
                if not self.id in list_of_clients:
                    list_of_clients.append(self.id)
                sock.sendall('-')
            except:
                if sock in connect_list:
                    connect_list.remove(sock)
                sock = socket(AF_INET, SOCK_STREAM)
                if self.id in list_of_clients:
                    list_of_clients.remove(self.id)

for x in range(num):
    if x != this_id:
        SendHandler(x,address).start()

while True:
    read_sockets, _ , _ = select.select([master_soc,this_soc],[],[])
    # can only accept one
    conn, addr = read_sockets[0].accept()
    # message from master
    if(read_sockets[0] == master_soc):
        ClientHandlerM(conn,addr).start()
    else:
        ClientHandlerS(conn,addr).start()

master_soc.close()
this_soc.close()
