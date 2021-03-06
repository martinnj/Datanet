#!/usr/bin/env python

import socket
import sys
import select
import errno

class ChatPeer:

    BUFFERSIZE = 1024

    def __init__(self):

        self.input_from = []
        self.nick = ''
        self.ns_socket = None

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
            req = sys.stdin.readline()
            self.parse_user_request(req)
            pass


    def connect_to_ns(self, ns_ip, ns_port):
        """
        Establish a connection to the name server and
        preform the required handshake
        """
        # You need to setup the connection and preform the handshake here.
        # First you should initiate the socket and connect to the name
        # server before starting the handshake

        self.ns_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ns_socket.connect((ns_ip , int(ns_port)))
        #print "Socket open"

        self.ns_socket.sendall("HELLO " + self.nick)
        resp = self.ns_socket.recv(self.BUFFERSIZE)
        tokens = resp.split()
        if tokens[0] == '100':
            print "Connected successfully to: " + ns_ip + ":" + ns_port
        if tokens[0] == '101':
            print "Nick " + self.nick + " was already taken."
            self.ns_socket.close()
            self.ns_socket = None
        if tokens[0] == '102':
            print "Handshake error, incomplete informatino."
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
            return tokens[2]
        elif tokens[0] == "201":
            print "User was not found."


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
            while i <= len(users)/2:
                print users[i] + " - " + users[i+1].replace(',','')
                i = i + 2
            #print users
        pass

# Run the server.
if __name__ == "__main__":
    ChatPeer().run()
