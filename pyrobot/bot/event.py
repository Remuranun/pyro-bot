import select
import sys
import time
import random
import socket
import os
from threading import Thread,Condition
from heapq import heappush, heappop, heapify

events = []
sockets = []

clientSockets = []
acceptedSockets = []
serverSockets = []

handlers = {}

waitcv = Condition()

def addEvent(event, delay):
    token = random.randint(0, sys.maxint)
    heappush(events, (time.time()+delay, event, token))
    waitcv.acquire()
    waitcv.notify()
    waitcv.release()
    return token

def removeEvent(token):
    global events
    before = len(events)
    events = filter(lambda (d, e, t): t != token, events)
    after = len(events)
    heapify(events)

def addSocket(socket, readFunction):
    global sockets
    sockets.append(socket)
    clientSockets.append(socket)
    handlers[socket]=readFunction
    waitcv.acquire()
    waitcv.notify()
    waitcv.release()

def setSocketHandler(socket, readFunction):
    global sockets
    if socket not in sockets:
        return
    handlers[socket]=readFunction
    
def removeSocket(socket):
    
    if (socket in sockets):
        sockets.remove(socket)
    if (socket in clientSockets):
        clientSockets.remove(socket)
    if (socket in acceptedSockets):
        acceptedSockets.remove(socket)
    #print 'removing',socket,sockets

        
#read function is in the readFunction(socket, data)
def addServerSocket(socket, readFunction):
    global sockets
    sockets.append(socket)
    serverSockets.append(socket)
    handlers[socket]=readFunction

def getTimeout():
    if events==[]:
        return -1.0
    else:
        now=time.time()
        nextTimer=events[0][0]
        return max(0.0, nextTimer-now)
    
def amain():
    while True:
        timeout = getTimeout();
        if timeout ==-1.0 and sockets == []:
            waitcv.acquire()
            waitcv.wait()
            waitcv.release()
            continue
        elif timeout==-1.0:
            ready=select.select(sockets, [], []);
        else:
            ready=select.select(sockets, [], [], timeout);
        for id in ready[0]:
            if (id in clientSockets):
                try:
                    handlers[id](id)
                except socket.error:
                    clientSockets.remove(id)
                    sockets.remove(id)
                    continue
                #except:
                    
                    #pass
            elif (id in acceptedSockets):
                data = id.recv(1024)
                if (data == ''):
                    acceptedSockets.remove(id)
                    sockets.remove(id)
                else:
                    handlers[id](id, data)

            elif (id in serverSockets):
                newsocket = id.accept()
                acceptedSockets.append(newsocket[0])
                handlers[newsocket[0]] = handlers[id]
                sockets.append(newsocket[0])
        
        while (getTimeout()==0.0):
            (_, handler, token)=heappop(events);
            handler()
            
#Run amain on a different thread
class EventProcessor(Thread):
    def run(self):
        amain()