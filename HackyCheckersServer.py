#!/usr/bin/env python3
# Server for the two hacky NOT AI clients
# -*- coding: utf-8 -*-

import os
import socket
import time
from threading import Thread, Event

# Taken from WOOF (Web Offer One File) by Simon Budig
# http://www.home.unix-ag.org/simon/woof
def find_ip():
    """Utility function to guess the IP where the server can be found from the network"""
    # we get a UDP-socket for the TEST-networks reserved by IANA.
    # It is highly unlikely, that there is special routing used
    # for these networks, hence the socket later should give us
    # the ip address of the default route.
    # We're doing multiple tests, to guard against the computer being
    # part of a test installation.
    
    candidates = []
    for test_ip in ["192.0.2.0", "198.51.100.0", "203.0.113.0"]:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((test_ip, 80))
        ip_addr = s.getsockname()[0]
        s.close()
        if ip_addr in candidates:
            return ip_addr
        candidates.append(ip_addr)
    
    return candidates[0]

# Set up port information
HOST = find_ip()
PORT = 8673#Un-assigned port
BUFSIZE = 1040
MAXCONNS = 2

class Client(Thread):
    """Client handling, given the socket, address, a name to use, a wait event, and chat data."""
    def __init__(self, socket, address, name, chatData):
        Thread.__init__(self)
        self.sock = socket
        self.addr = address
        self.name = name
        self.data = chatData
        self.active = False
        self.recvData = None
        self.timer = None
        self.lastMsg = float(time.time())
        self.start()
    
    def run(self):
        self.active = True
        while self.active:
            try:
                self.recvData = self.sock.recv(BUFSIZE)
            except OSError as e:
                self.data.append([self.name, '[S] bye'])
                self.active = False
            else:
                if not self.recvData or self.recvData == b'' or closeWaitEvent.is_set():
                    self.data.append([self.name, '[S] bye'])
                    self.active = False
                else:
                    for i in self.recvData.decode('utf-8').split(';'):
                        self.data.append([self.name, i])
            self.lastMsg = float(time.time())
        self.sock.close()
        print('Client Connection Terminated', file=os.sys.stderr)
    
    def send_all(self, data):
        if self.active:
            self.sock.sendall(data)
    pass

class ClientTimer(Thread):
    def __init__(self, clients, clientId, waitTime, wakeupMsg=''):
        Thread.__init__(self)
        self.clients = clients
        self.cid = clientId
        self.timer = float(waitTime)
        self.wakeup = bool(wakeupMsg)
        self.msg = ('[%s] %s;' % (str(self.cid), str(wakeupMsg))).encode('utf-8')
        self.start()
    
    def run(self):
        if self.cid in self.clients:
            client = self.clients[self.cid]
        else:
            print('Server: ClientTimer: Error: Client Id is Invalid', file=os.sys.stderr)
            return
        while client.active:
            elapsedTime = float(time.time()) - client.lastMsg
            if elapsedTime >= self.timer:
                if self.wakeup:
                    try:
                        print('Server: ClientTimer: Timer over; Sent "%i" Wakeup Message.' % self.cid)
                        client.send_all(self.msg)
                    except OSError:
                        print('Server: ClientTimer: Error Occored when sending "%i" wakeup message' % self.cid, file=os.sys.stderr)
                        time.sleep(0.5)
                    else:
                        client.lastMsg = float(time.time())
                else:
                    print('Server: ClientTimer: No Message, Closing Client Socket.')
                    client.sock.close()
            else:
                time.sleep(1)
        print('Server: ClientTimer: Client is Inactive, exiting')
    pass

def getServer():
    # Initialize the socket
    s = socket.socket()
    
    print('Server: Attempting to bind socket to %s on port %i...' % (HOST, PORT))

    # Bind the socket to a local address.
    s.bind((HOST, PORT))
        
    # Enable a server to accept connections.
    # specifies the number of unaccepted connections that the
    # system will allow before refusing new connections.
    s.listen(MAXCONNS)
    return s

def run():
    global clients
    global closeWaitEvent
    global serversocket
    global chatData
    clients = {}
    closeWaitEvent = Event()
    # Set up a list to hold chat data
    chatData = []
    
    # Get the ip address we are working on
    ip_addr = ':'.join([str(i) for i in serversocket.getsockname()])
    
    print('Server: Server and running on', ip_addr)
    print('Server: Awaiting %i connections.' % MAXCONNS)
    
    # Server should only permit a certain number of connections; No more, no less
    cid = 0
    idToAddr = {}
    # While there are spots to be filled,
    while len(clients) < MAXCONNS:
        # Accept any new connections
        clientSock, addr = serversocket.accept()
        print('Server: New Connection', addr, 'id is', cid)
        print('Server:', cid+1, 'of', MAXCONNS, 'Connections Achieved')
        # Remember the address based on client id
        idToAddr[cid] = addr
        # Initialize a new client thread and add it to the list of clients
        clients[cid] = Client(clientSock, addr, int(cid), chatData)
        # Increment the client id value
        cid += 1
    print('Server: All connections established.')
    print('Server: Sending confermation message to clients...')
    # Tell all connected clients all connected users
    # Get the client names and seperate them by slashes
    clientNames = '/'.join([str(i) for i in clients.keys()])
    # For each connected client,
    for client in clients.values():
        # Get the text ready to send
        send = 'You: "%s" Clients: "%s";' % (str(client.name), clientNames)
        # Send the text to the client with the utf-8 encoding
        client.send_all(send.encode('utf-8'))
    print('Server: Message sent.')
    print('Server: Beginning Chat...')
    # While no inactive clients exist,
    while not (False in [client.is_alive() for client in clients.values()]):
        try:
            # If there is chat data,
            if chatData:
                # For each message, print it
                for i in ['From: "'+str(i[0])+'" : '+i[1] for i in chatData]:
                    print('Server:', i)
                # Seperate message data from client id data
                messages = [i[1]+';' for i in chatData]
                # Get the "To" address lines from each message
                to_ids = [m.split(' ')[0][1:-1] for m in messages]
                words = sum([i.split(' ') for i in sum([i.lower().split(';') for i in messages], [])], [])
                close = False
                # If there are messages addressed to server,
                if 'S' in to_ids:
                    for idx in range(len(to_ids)):
                        if to_ids[idx] == 'S':
                            # Get the server message
                            srvrmsg = messages[idx]
                            msglst = [i for i in sum([i.split(' ') for i in srvrmsg.split(';')], [])]
                            # If the message contains the word 'bye',
                            if len(msglst) >= 3 and msglst[1].lower() == 'wakeup' and msglst[2].isnumeric():
                                print('Server: Starting Wakeup Thread for Client "%s"' % chatData[idx][0]) 
                                cid = int(chatData[idx][0])
                                wait, wkupmsg = float(msglst[2]), ' '.join(msglst[3:-1])
                                ClientTimer(clients, cid, wait, wkupmsg)
                    if close:
                        break
                if 'bye' in words:
                    # Close the server.
                    print("Server: Client said 'bye'. Closing server.")
                    close = True
                    break

                # For each client,
                for client in iter(clients.values()):
                    # Get the client's id
                    cid = client.name
                    # For each message
                    for frm, msg in chatData:
                        # Split the message by spaces
                        data = msg.split(' ')
                        # If the to address equals the client's id,
                        if data[0][1:-1] == str(cid):
                            # Modify the message to say who sent it instead of who it's for,
                            # since a client won't get a message if it's not addressed to
                            # them (duh)
                            data[0] = '[%s]' % frm
                            send = ' '.join(data)+';'
                            # Send that client the message
                            print('Server: Sending', cid, 'Message', send)
                            client.send_all(send.encode('utf-8'))
                # When done processing chat data, delete it all
                del chatData[:]
        except KeyboardInterrupt:
            break
    # Once there is an inactive client,
    for client in clients.values():
        # Tell all clients to disconnect
        client.send_all(b';bye')
    # Close the server socket
    serversocket.close()
    # Tell all client threads that may still be active to close
    closeWaitEvent.set()
    print('Server: Server shutting down... Waiting five secconds for all threads to stop.')
    time.sleep(5)
    # Find any clients that didn't listen
    alives = [i for i in clients.values() if i.is_alive()]
    # If any threads aren't listening,
    if alives:
        print('Server: %i client(s) is still active!' % len(alives), file=os.sys.stderr)
        # Tell all alive clients to close their sockets
        for client in alives:
            client.sock.close()
        # Try to wait for child processes to quit
        print('Server: Attempting to wait for child processes to quit...')
        try:
            os.wait()
        except ChildProcessError as e:
            # If it breaks (most of the time because everything quit),
            # Print the error message
            print('Server: ChildProcessError:', e, file=os.sys.stderr)
    print('Server: All connections SHOULD now be terminated.')

if __name__ == '__main__':
    try:
        serversocket = getServer()
    except OSError as e:
        print('Server:', str(e), file=os.sys.stderr)
        input('Server: Press Enter to Continue.\n')
    else:
        try:
            run()
        except BaseException as e:
            print('Server:', e, file=os.sys.stderr)
    # Ensure the server socket closes no matter what.
    try:
        serversocket.close()
    except BaseException:
        pass
