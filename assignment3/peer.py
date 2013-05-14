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
                    req = sys.stdin.readline()
                    self.parse_user_request(req)
                elif inp == self.listener:
                    self.connect_from_peer(inp)
                else:
                    self.handle_input(inp)
            pass

    def handle_input(self, sock):
        """
        Handle input coming from a peer socket
        """
        req = "" + sock.recv(self.BUFFERSIZE)
        self.parse_peer_request(self, req, sock)

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
        print "Will listen on: localhost:" + str(listen_port)
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
                print "Left Name Server"
            else:
                print "Error: not connected"

        elif tokens[0] == "/quit":
            print "Shutting down"
            sys.exit(0)

        elif tokens[0] == "/lookup":
            #For testing only, may not be directly callable.
            ip = self.lookup_peer(tokens[1])
            print "Lookup returned: " + str(ip)
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
            i = 0;
            while i <= len(users)/3:
                print users[i] + " - " + users[i+1] + ":" + users[i+2].replace(',','')
                i = i + 3
            #print users
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
        pass


    def connect_from_peer(self, sock):
        """
        Accept a connection from a connecting peer
        and preform the required handshake
        """
        # This method is basically the opposite of the above one.
        # Here you need to accept and incoming peer connection
        # and preform the receiver part of the peer-peer handshake.
        pass


    def parse_peer_request(self, request, sock):
        """
        Parse a request from a connected peer and preform the appropriate actions
        """
        parts = request.split()

        if len(parts) > 0 and parts[0] == "MSG":
            # Do the appropriate actions according to the protocol.
            pass
        elif len(parts) > 0 and parts[0] == "LEAVE":
            # Do the appropriate actions according to the protocol.
            pass
        else:
            print "Unrecognized command '%s' from peer %s ignored" % \
                (data, self.socks2nicks[sock])
            # Remember to send a response indicating bad formating


    def disconnect_from_peers(self):
        """
        Close the connection properly to all connected peers
        """
        # Here you should close the connection to all peers
        # that are currently connected.
        # Remember to send the appropriate leave requests.
        pass

    def send_message(self, user, msg):
        """
        Send a message to a peer that is already connected to
        """
        # Here you should send a message to a connected peer.
        # Remember to check if you receive a message ack.
        pass

    def broadcast(self, msg):
        """
        Broadcast a message to all users in the system. Establishing
        connections to peers is also a part of this function.
        """
        # Here you should first make sure that you have established a
        # connection to all peers on the system.
        # When these connections are obtained, you should send the message
        # to every peer like you would send a regular message.
        pass


# Run the server.
if __name__ == "__main__":
    ChatPeer().run()
