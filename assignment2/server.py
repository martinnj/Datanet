#!/usr/bin/env python2

import socket
import select
import logging

class ChatNameServer:

    BUFFERSIZE = 1024

    def __init__(self):

        self.input_from = []
        self.names2info = {}
        self.socks2names = {}

        # You should change these settings if not running the service locally
        ns_ip = 'localhost'
        ns_listen_port = 6789

        logging.basicConfig( level=logging.DEBUG
                           , format = '[%(asctime)s] %(levelname)s: %(message)s'
                           )

        self.logger = logging.getLogger('NameServer')

        self.logger.info('Service initialized')

        # Here you should setup the socket needed for listening for incoming
        # peers trying to connect
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((ns_ip,ns_listen_port))
        self.server.listen(10)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.input_from.append(self.server)

    def run(self):
        """
        The main loop of the name server
        """
        running = True

        while(running):
            # This is the main loop of the name server
            #
            # This loop needs to:
            #
            # - Listen for new sockets and create a connection to these
            # - Listen for new request from already connected users
            # - Detect dead sockets and remove these

            (rsocks, wsocks, esocks) = select.select(self.input_from,[],[])
            for sock in rsocks:
                if sock is self.server:
                    csock , caddr = self.server.accept()
                    self.connect_to_peer(csock,caddr)
                else:
                    req = sock.recv(self.BUFFERSIZE)
                    #print req
                    if req != "":
                        self.parse_request(req, sock)
                    else:
                        nick = self.socks2names[sock]
                        self.logger.info("" + nick + " Disconnected by him/herself.")
                        del self.names2info[nick]
                        del self.socks2names[sock]
                        self.input_from.remove(sock)
                        sock = None
                    pass


    def connect_to_peer(self, sock, addr):
        """
        Establish a connection to a new peer and
        preform the required handshake
        """

        # You need to setup the connection and preform the handshake here.
        # First you should accept the socket before starting the handshake
        request = sock.recv(self.BUFFERSIZE)
        tokens = request.strip().split()
        if tokens[0] == 'HELLO' and len(tokens) == 2:
            #Do a check if name is taken.
            if tokens[1] in self.names2info:
                self.logger.info("101 Rejection for " + addr[0])
                sock.sendall("101 TAKEN")
                sock.close
                sock = None
            else:
                self.names2info[tokens[1]] = (sock, addr[0], addr[1])
                self.socks2names[sock] = tokens[1]
                self.logger.info("100 connected to " + addr[0] + ":" + str(addr[1]))
                self.input_from.append(sock)
                sock.sendall("100 CONNECTED")
        else:
            self.logger.info("102 Rejection for " + addr[0])
            sock.sendall("102 HANDSHAKE EXPECTED")
            sock.close
            sock = None
        pass


    def parse_request(self, request, sock):
        """
        Parse a request from a peer and preform the appropriate actions
        """
        tokens = request.split()

        if tokens[0] == "USERLIST":
            self.logger.info("User requested userlist")
            self.send_userlist(sock)

        elif tokens[0] == "LOOKUP" and len(tokens) == 2:
            self.logger.info("user requested lookup of user %s" % tokens[1])
            self.lookup_user(tokens[1],sock)

        elif tokens[0] == "LEAVE":
            self.logger.info("User wishes to leave service")
            self.leave_peer(sock)
        else:
            sock.sendall("500 BAD FORMAT")
            self.logger.info("Unrecognized command '%s' ignored" % request)
            # Remember to send a response indicating bad formating


    def lookup_user(self,nick, sock):
        """
        Lookup a user on the name server
        """
        if nick in self.names2info:
            # Send the appropriate response according to the protocol
            sock.sendall("200 INFO " + self.names2info[nick][1])
        else:
            # Send the appropriate response according to the protocol
            sock.sendall("201 USER NOT FOUND")
            pass



    def send_userlist(self, sock):
        """
        Send a list of all online users. Response should comply with the protocol
        """
        # Here you should examine the list of connected peers
        # and determine how many peers is connected.
        # You will need to form the responce according to the protocol.
        # Remenber that the user requesting the list shouldn't be on the list.
        if len(self.names2info) == 1:
            sock.sendall("301 ONLY USER")
        else:
            resp = "300 INFO " + str(len(self.names2info))
            for socket in self.socks2names:
                if socket is not sock:
                    name = self.socks2names[socket]
                    resp = resp + " " + name + " " + self.names2info[name][1] + ","
            sock.sendall(resp[:-1])

    def leave_peer(self, sock):
        """
        Close the connection properly to a leaving peer
        """
        # Here you need to send the proper response to the leaving peer
        # and then close the socket and remove the peer from the system
        sock.sendall("400 BYE")
        sock.close()
        nick = self.socks2names[sock]
        self.logger.info("Disconnecting " + nick)
        del self.names2info[nick]
        del self.socks2names[sock]
        self.input_from.remove(sock)
        sock = None
        pass


# Run the server.
if __name__ == "__main__":
    ChatNameServer().run()
