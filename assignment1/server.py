#!/usr/bin/env python2


import socket
import select
import sys
import thread
from datetime import datetime
import errno

class Server:
    BUFFER_SIZE = 1024
    def __init__(self, port=50000, listen_queue_size=5):
        """
        Initialize the variables required by the name server.
        """

        self.port = port

        self.server = None #use this variable as the server socket


        # Initialize the socket and data structures needed for the server.
        #
        # Set the socket options to allow reuse of the server address, bind
        # the socket and listen for connections .
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('',self.port))
        self.server.listen(listen_queue_size)
        #self.server.setblocking(0)

    def is_float(self,f):
        try:
            float(f)
            return True
        except ValueError:
            return False

    def parse_command(self, command, sock):
        """
        Parse the incomming data and act accordingly.
        """

        tokens = command.strip().split()

        #if PING
        if len(tokens) == 1 and tokens[0] == 'PING':
            sock.send("100 PONG (" + sock.getpeername()[0] + ":" +
                      str(sock.getpeername()[1]) + ") " + str(datetime.now()))
            pass
        #if CALC
        if len(tokens) == 4 and tokens[0] == 'CALC':
            if self.is_float(tokens[1]) and self.is_float(tokens[3]) and not(tokens[2] not in "+-*/"):
                op1 = float(tokens[1])
                op2 = float(tokens[3])
                op = tokens[2]
                if op is "+":
                    res = op1 + op2
                elif op is "-":
                    res = op1 - op2
                elif op is "*":
                    res = op1 * op2
                elif op is "/":
                    res = op1 / op2
                sock.send("200 EQUALS " + str(res))
            else:
                sock.send("201 NAN")
            pass

        #if ECHO
        #the below if is looking at the command string instead of the tokens list to allow for whitespaces
        #since the command variable is not stripped
        if len(command) > 5 and command[:5].upper() == 'ECHO ':
            sock.send("300 " + command[5:])
            pass

        return '400 BAD FORMAT'

    def handle_client(self, socket, address):
        while 1:
            data = socket.recv(self.BUFFER_SIZE)
            if not data: break
            self.parse_command(data,socket)
        socket.close()


    def run(self):
        """
        The main loop of the server.
        """
        running = True

        while running:
            # This loop should:
            #
            # - Accept new connections.
            #
            # - Read any socket that wants to send information.
            #
            # - Respond to messages that are received according to the rules in
            # the protocol. Any message that does not adhere to the protocol
            # will trigger an error message
            #
            # - Clean up sockets that are dead.

            (csock,caddr) = self.server.accept()
            thread.start_new_thread(self.handle_client,(csock,caddr))
            #running = False
        # Close the server socket when exiting.
        #print "Closing server"
        self.server.close()
        self.server = None

#run the server
if __name__ == "__main__":
    try:
        Server().run()
    except Exception as e:

        print e
