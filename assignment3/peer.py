#!/usr/bin/env python2

import socket
import sys
import select
import errno
import random

class ChatPeer:

    BUFFERSIZE = 1024

    def __init__(self):

        self.input_from = []
        self.sock2nick = {}
        self.nick2info = {}
        self.nick = ''
        self.ns_socket = None
        self.listener = None

        # Append stdin to the list of inpt sources
        # NOTE: this is only possible in Unix based system. If you are using
        # Windows you can't do this trick.
        self.input_from.append(sys.stdin)

    def run(self):
        """
        The main loop of the peer
        """

        running = True

        while(running):
            # Print a simple prompt.
            sys.stdout.write('\n> ')
            sys.stdout.flush()

            # This is the main loop of the peer
            #
            # This loop needs to:
            #
            # - Listen for new requests from the user (via stdin)
            # - Detect whether the socket to the name server has died
            #req = sys.stdin.readline()
            #self.parse_user_request(req)
            (rl, wl, el) = select.select(self.input_from,[],[])
            for inp in rl:
                if inp == sys.stdin:
                    #print "msg from stdin"
                    req = sys.stdin.readline()
                    self.parse_user_request(req)
                elif inp == self.listener:
                    #print "msg from listener"
                    self.connect_from_peer(inp)
                else:
                    #print "msg from peer"
                    self.handle_input(inp)
            pass

    def handle_input(self, sock):
        """
        Handle input coming from a peer socket
        """
        req = sock.recv(self.BUFFERSIZE)
        if req != "":
            self.parse_peer_request(req, sock)
        else:
            nick = self.sock2nick[sock]
            print nick + " disconnected"
            del self.nick2info[nick]
            del self.sock2nick[sock]
            self.input_from.remove(sock)
            sock = None

    def connect_to_ns(self, ns_ip, ns_port):
        """
        Establish a connection to the name server and
        preform the required handshake
        """
        # You need to setup the connection and preform the handshake here.
        # First you should initiate the socket and connect to the name
        # server before starting the handshake

        listen_ip = 'localhost'
        # TODO: find a way to let socket choose the port.
        listen_port = int(ns_port) + random.randint(200,20000)
        #this gives 19800 different ports,  should be enough for this assignment :)
        #print "Will listen on: localhost:" + str(listen_port)
        self.ns_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ns_socket.connect((ns_ip , int(ns_port)))
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind((listen_ip,listen_port))
        self.listener.listen(10)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.input_from.append(self.listener)
        #print "Socket open"

        self.ns_socket.sendall("HELLO " + self.nick + " " + str(listen_port))
        resp = self.ns_socket.recv(self.BUFFERSIZE)
        tokens = resp.split()
        if tokens[0] == '100':
            print "Connected successfully to: " + ns_ip + ":" + ns_port
        if tokens[0] == '101':
            print "Nick " + self.nick + " was already taken."
            self.ns_socket.close()
            self.ns_socket = None
        if tokens[0] == '102':
            print "Handshake error, incomplete information."
            self.ns_socket.close()
            self.ns_socket = None

        pass

    def disconnect_from_ns(self):
        """
        Close the connection properly to the name server
        """
        # Here you should send the appropriate message to the name server
        # letting it know that you are leaving. When getting the correct
        # response your peer should close the socket and set the ns_socket
        # to None.
        self.ns_socket.sendall("LEAVE")
        resp = self.ns_socket.recv(self.BUFFERSIZE)
        self.ns_socket.close()
        self.ns_socket = None
        pass

    def parse_user_request(self, request):
        """
        Parse a request from the user and preform the appropriate actions
        """
        # Please note: in this function we are using the ns_socket to
        # check whether we are connected or not. It is therefor important that
        # the ns_socket is set to None when we don't have a connection.

        tokens = request.split()

        if tokens[0] == "showme":
            print self.nick2info
            print self.sock2nick
        if tokens[0] == "/connect" and len(tokens) == 3:
            if self.nick == "":
                print "Error: you need to chose a nick name before connecting"
            elif self.ns_socket:
                print "Error: you are already connected to a name server"
            else:
                self.connect_to_ns(tokens[1], tokens[2])

        elif tokens[0] == "/nick" and len(tokens) == 2:
            if ',' in tokens[1]:
                print "Error: can't pick a nick name with ',' in it"
            else:
                self.nick = tokens[1]
                print 'Nick changed to ' + self.nick

        elif tokens[0] == "/userlist":
            if self.ns_socket:
                self.print_users()
            else:
                print "Error: not connected"

        elif tokens[0] == "/leave":
            if self.ns_socket:
                self.disconnect_from_ns()
                self.disconnect_from_peers()
                print "Left Name Server"
            else:
                print "Error: not connected"

        elif tokens[0] == "/quit":
            print "Shutting down"
            sys.exit(0)

        #elif tokens[0] == "/lookup" and len(tokens) == 2:
        #    #For testing only, may not be directly callable.
        #    ip = self.lookup_peer(tokens[1])
        #    print "Lookup returned: " + str(ip)

        elif tokens[0] == "/msg":
            self.send_message(tokens[1], " ".join(tokens[2:]))

        elif tokens[0] == "/all":
            self.broadcast(" ".join(tokens[1:]))
        else:
            print "Error: unknown message format"


    def lookup_peer(self, user):
        """
        Query the name server for information on a user by it's nick
        """
        # Here you should do a lookup request to the name server on a specific
        # user and return the proper information if that user is connected to
        # the service.
        #
        # Note that this method should not be directly callable for the user.
        # You will need it for the next assignment.
        self.ns_socket.sendall("LOOKUP " + user)
        data = self.ns_socket.recv(self.BUFFERSIZE)
        tokens = data.split()
        if tokens[0] == "200":
            # add user to list before returning.
            self.nick2info[user] = [None,tokens[2], tokens[3]]
            return tokens[2] + ":" + tokens[3]
        elif tokens[0] == "201":
            print "User " + user + " was not found."


    def print_users(self):
        """
        Get the list of online users and print it using nice formating
        """
        # Here you should make a request to the name server and receive
        # the list of online users from it.
        # You should then format this list and show it to the user.
        # Remember to put the current user on the list as well.
        self.ns_socket.sendall("USERLIST")
        data = self.ns_socket.recv(self.BUFFERSIZE)
        resp = str(data)
        print "Online Users:"
        print ""
        print self.nick + " - You"
        if resp[:3] == "300":
            users = resp.split()[3:]
            #print users
            i = 0;
            while i <= (len(users)/3)+1:
                nick = users[i]
                ip = users[i+1]
                port = users[i+2].replace(',','')
                print nick + " - " + ip + ":" + port
                if self.nick2info.get(nick,None) == None:
                    self.nick2info[nick] = [None,ip, port]
                i = i + 3
        pass




# ---------------------------------------------------------------------
# ------------------ NEW METHODS FOR ASSIGNMENT 3 ---------------------
# ---------------------------------------------------------------------
#
# These new methods should be appended to the existing peer.py
# implementation you made last week


    def connect_to_peer(self, user_nick, user_addr):
        """
        Establish a connection to a peer and
        preform the required handshake
        """
        # Here you should preform the connection to a new peer.
        # You should connect a new socket to the peer and preform the
        # peer-peer handshake.
        info = user_addr.split(':')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((info[0] , int(info[1])))
        sock.sendall("HELLO " + self.nick)
        data = "" + sock.recv(self.BUFFERSIZE)
        tokens = data.split()
        if tokens[0] == "100":
            self.nick2info[user_nick] = [sock,info[0],info[1]]
            self.sock2nick[sock] = user_nick
            self.input_from.append(sock)
            #DEBUG INFO:
            #print "Connected to peer."
        else:
            print "Could not connect to peer." + " ".join(tokens[0:])
        pass


    def connect_from_peer(self, sock):
        """
        Accept a connection from a connecting peer
        and preform the required handshake
        """
        # This method is basically the opposite of the above one.
        # Here you need to accept and incoming peer connection
        # and preform the receiver part of the peer-peer handshake.
        csock , caddr = sock.accept()
        request = csock.recv(self.BUFFERSIZE)
        #print "new peer wrote: " + request
        tokens = request.strip().split()
        if tokens[0] == 'HELLO' and len(tokens) == 2:
            #Do a check if name is in use
            if self.nick2info.get(tokens[1],None) is not None:
                csock.sendall("101 REFUSED")
                csock.close
                csock = None
            else:
                self.nick2info[tokens[1]] = [csock,caddr[0],caddr[1]]
                self.sock2nick[csock] = tokens[1]
                #self.logger.info("100 connected to " + addr[0] + ":" + str(addr[1]))
                self.input_from.append(csock)
                csock.sendall("100 CONNECTED")
                #DEBUG:
                #print "connection from new peer!"
        else:
            csock.sendall("102 HANDSHAKE EXPECTED")
            csock.close
            csock = None
        pass


    def parse_peer_request(self, request, sock):
        """
        Parse a request from a connected peer and preform the appropriate actions
        """
        parts = request.split()

        if len(parts) > 0 and parts[0] == "MSG":
            # Do the appropriate actions according to the protocol.
            print "" + self.sock2nick[sock] + ": " + " ".join(parts[1:])
            sock.sendall("200 MSG ACK")
        elif len(parts) > 0 and parts[0] == "LEAVE":
            # Do the appropriate actions according to the protocol.
            sock.sendall("400 BYE")
            print "" + self.sock2nick[sock] + " left."
            sock.close()
            nick = self.sock2nick[sock]
            del self.nick2info[nick]
            del self.sock2nick[sock]
            self.input_from.remove(sock)
            sock = None
        else:
            print "Unrecognized command '%s' from peer %s ignored" % \
                (request, self.sock2nick[sock])
            # Remember to send a response indicating bad formating
            sock.sendall("500 BAD FORMAT")


    def disconnect_from_peers(self):
        """
        Close the connection properly to all connected peers
        """
        # Here you should close the connection to all peers
        # that are currently connected.
        # Remember to send the appropriate leave requests.
        for nick in self.nick2info:
            info = self.nick2info.get(nick,None)
            if info is not None:
                if info[0] is not None:
                    sock = info[0]
                    sock.sendall("LEAVE")
                    sock.close()
                    #nick = self.sock2nick[sock]
                    #del self.nick2info[nick]
                    #del self.sock2nick[sock]
                    self.input_from.remove(sock)
                    sock = None
        self.nick2info = {}
        self.sock2nick = {}
        pass

    def send_message(self, user, msg):
        """
        Send a message to a peer that is already connected to
        """
        # Here you should send a message to a connected peer.
        # Remember to check if you receive a message ack.
        info = self.nick2info.get(user,None)
        sock = None
        if info is not None:
            if info[0] is not None:
                #we got socket
                sock = info[0]
                #print "1: " + info[1]
            else:
                #got info, get socket
                addr = "" + info[1] + ":" + info[2]
                self.connect_to_peer(user,addr)
                #print "2: " + info[1]
                self.nick2info[user][0] = sock
            pass
        else:
            #lookup from scratch
            self.lookup_peer(user)
            info = self.nick2info.get(user,None)
            addr = "" + info[1] + ":" + info[2]
            self.connect_to_peer(user,addr)
            #print "3: " + info[1]
            sock = self.nick2info[user][0]

        # Ready to send message!
        sock.settimeout(10.0) # give 10 seconds timeout on chat message
        sock.sendall("MSG " + msg)
        resp = sock.recv(self.BUFFERSIZE)
        if resp is None or resp.split()[0] != "200":
            print "Message was not delivered to " + user + "!"

    def broadcast(self, msg):
        """
        Broadcast a message to all users in the system. Establishing
        connections to peers is also a part of this function.
        """
        # Here you should first make sure that you have established a
        # connection to all peers on the system.
        # When these connections are obtained, you should send the message
        # to every peer like you would send a regular message.
        self.ns_socket.sendall("USERLIST")
        data = self.ns_socket.recv(self.BUFFERSIZE)
        resp = str(data)
        if resp[:3] == "300":
            users = resp.split()[3:]
            i = 0;
            while i <= (len(users)/3)+1:
                nick = users[i]
                ip = users[i+1]
                port = users[i+2].replace(',','')
                self.connect_to_peer(nick, ip + ":" + port)
                i = i + 3
        for nick in self.nick2info:
            self.send_message(nick, msg)


# Run the server.
if __name__ == "__main__":
    ChatPeer().run()
