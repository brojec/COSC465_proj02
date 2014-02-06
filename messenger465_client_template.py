#!/usr/bin/env python

__author__ = "jsommers@colgate.edu.  Edited by Carrie and Brett"
__doc__ = '''
A simple model-view controller-based message board/chat client application.
'''

import sys
import Tkinter
import socket
from select import select
import argparse
from time import ctime

def mb_checksum(string):
	check = 0;
	for i in string:
		check = check^ord(i);
	return chr(check);


class MessageBoardNetwork(object):
	'''
	Model class in the MVC pattern.  This class handles
	the low-level network interactions with the server.
	It should make GET requests and POST requests (via the
	respective methods, below) and return the message or
	response data back to the MessageBoardController class.
	'''
	#Carrie & Brett
	def __init__(self, host, port, retries, timeout):
		'''        
		Constructor.  You should create a new socket
		here and do any other initialization.
		CHECK!!
		'''
		self.host = host
		self.port = port
		self.retries = retries
		self.timeout = timeout
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.version = 'C'
		self.recvnum = 1400
		self.seq = 0;
	

	#Carrie & Brett
	def getMessages(self):
		'''
	        You should make calls to get messages from the message 
		board server here.
		'''
		for i in range(0,self.retries+1):
			self.sock.sendto((self.version + str(self.seq) + mb_checksum("GET")+'GET'), (self.host, self.port))
			thetime = select([self.sock], [], [], self.timeout)[0]
			if thetime == []: #changed from thetime[0]
			        if i==self.retries:
				        raise socket.error('timeout');
			else:
				result = self.sock.recvfrom(self.recvnum)[0]
				self.seq = self.seq^1; #flipping bit b/w 0 and 1
				break;
                if result[0] != self.version:
                    raise socket.error('version mismatch, received {0}'.format(self.version))
                result = result[1:]
                if result[0] == self.seq: #seq can only be 1 or 0, and we already flipped it
                    raise socket.error('sequence mismatch, on sequence {0}, received sequence {1}'.format(self.seq^1, result[0]))
                result = result[1:]
                if result[0] != mb_checksum(result[1:]):
                    raise socket.error('checksum failure')
                result = result[1:]
		returnlist = result.split('::') #break up by ::
		if(returnlist[0][0:2]!='OK'):
			raise socket.error(returnlist)
		returnlist[0] = returnlist[0][3:] #getting rid of leading data
		newlist = []
		for i in range(0,len(returnlist),3):
			newlist.append(' '.join(returnlist[i:i+3]))
		return newlist

#Brett
	def postMessage(self, user, message):
		for i in range(0,self.retries+1):
                        ps = '{0}{1}{2}POST {3}::{4}'.format(self.version, self.seq, mb_checksum(message),user, message)
                        print 'posting message: {0}'.format(ps)
			self.sock.sendto(ps,(self.host, self.port))
                        time = select([self.sock], [], [], self.timeout)[0]
			if time == []: #changed from time[0]
			        if i==self.retries:
			                print 'entered timeout for post'
			                raise socket.error('timeout')
			else:
			        print 'received ACK I think...'
				resp = self.sock.recvfrom(self.recvnum)[0]
                                print 'server response to POST: {0}'.format(resp)
                                self.seq = self.seq^1;
                                if resp[0] != self.version:
                                    raise socket.error('version mismatch, received {0}'.format(resp[0]))
                                resp = resp[1:]
                                if resp[0] == self.seq:
                                    raise socket.error('sequence mismatch, received sequence {0}'.format(resp[0]))
                                resp = resp[1:]
                                if resp[0] != mb_checksum(resp[1:]):
                                    raise socket.error('checksum failure')
                                resp = resp[1:]
                                if resp[0:2] != "OK":
                                    raise socket.error(resp)


class MessageBoardController(object):
	'''
	Controller class in MVC pattern that coordinates
	actions in the GUI with sending/retrieving information
	to/from the server via the MessageBoardNetwork class.
	'''

	def __init__(self, myname, host, port, retries, timeout):
		self.name = myname
		self.view = MessageBoardView(myname)
		self.view.setMessageCallback(self.post_message_callback)
		self.net = MessageBoardNetwork(host, port, retries, timeout)

	def run(self):
		self.view.after(1000, self.retrieve_messages)
		self.view.mainloop()

	#Brett
	def post_message_callback(self, m):
		if(len(self.name)>8):
			self.view.setStatus("User name >8 characters")
			return;
		elif(len(m)>60):
			self.view.setStatus("Message >60 characters")
			return;
		elif('::' in self.name or '::' in m):
			self.view.setStatus("message, username cannot contain '::'");
			return;
		try:
			print 'posting message'
                        self.net.postMessage(self.name, m);
		except socket.error as err:
			self.view.setStatus(err.message);
	

	#Carrie
	def retrieve_messages(self):
	        '''
	        This method gets called every second for retrieving
	        messages from the server.  It calls the MessageBoardNetwork
	        method getMessages() to do the "hard" work of retrieving
	        the messages from the server, then it should call 
	        methods in MessageBoardView to display them in the GUI.

	        You'll need to parse the response data from the server
	        and figure out what should be displayed.

	        Two relevant methods are (1) self.view.setListItems, which
	        takes a list of strings as input, and displays that 
	        list of strings in the GUI, and (2) self.view.setStatus,
	        which can be used to display any useful status information
	        at the bottom of the GUI.
	        '''
	
	        '''
	        In getMessages(), we concatonated the strings into groups of
	        "user time message"
	        '''
	        try:
		        alist = self.net.getMessages()
		        self.view.setListItems(alist)
	        except socket.error as err:
		        self.view.setStatus(err.message)
	        self.view.after(1000, self.retrieve_messages)
	        messagedata = self.net.getMessages()


class MessageBoardView(Tkinter.Frame):
	'''
	The main graphical frame that wraps up the chat app view.
	This class is completely written for you --- you do not
	need to modify the below code.
	'''
	def __init__(self, name):
		self.root = Tkinter.Tk()
		Tkinter.Frame.__init__(self, self.root)
		self.root.title('{} @ messenger465'.format(name))
		self.width = 80
		self.max_messages = 20
		self._createWidgets()
		self.pack()

	def _createWidgets(self):
		self.message_list = Tkinter.Listbox(self, width=self.width, height=self.max_messages)
		self.message_list.pack(anchor="n")

		self.entrystatus = Tkinter.Frame(self, width=self.width, height=2)
		self.entrystatus.pack(anchor="s")

		self.entry = Tkinter.Entry(self.entrystatus, width=self.width)
		self.entry.grid(row=0, column=1)
		self.entry.bind('<KeyPress-Return>', self.newMessage)

		self.status = Tkinter.Label(self.entrystatus, width=self.width, text="starting up")
		self.status.grid(row=1, column=1)

		self.quit = Tkinter.Button(self.entrystatus, text="Quit", command=self.quit)
		self.quit.grid(row=1, column=0)


	def setMessageCallback(self, messagefn):
		'''
		Set up the callback function when a message is generated 
		from the GUI.
		'''
		self.message_callback = messagefn

	def setListItems(self, mlist):
		'''
		mlist is a list of messages (strings) to display in the
		window.  This method simply replaces the list currently
		drawn, with the given list.
		'''
		self.message_list.delete(0, self.message_list.size())
		self.message_list.insert(0, *mlist)
	
	def newMessage(self, evt):
		'''Called when user hits entry in message window.  Send message
		to controller, and clear out the entry'''
		message = self.entry.get()  
		if len(message):
			self.message_callback(message)
		self.entry.delete(0, len(self.entry.get()))

	def setStatus(self, message):
		'''Set the status message in the window'''
		self.status['text'] = message

	def end(self):
		'''Callback when window is being destroyed'''
		self.root.mainloop()
		try:
			self.root.destroy()
		except:
			pass

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='COSC465 Message Board Client')
	parser.add_argument('--host', dest='host', type=str, default='localhost',
			help='Set the host name for server to send requests to (default: localhost)')
	parser.add_argument('--port', dest='port', type=int, default=1111,
			help='Set the port number for the server (default: 1111)')
	parser.add_argument("--retries", dest='retries', type=int, default=3,
                        help='Set the number of retransmissions in case of a timeout')
	parser.add_argument("--timeout", dest='timeout', type=float, default=0.1,
                        help='Set the RTO value')
                        
	args = parser.parse_args()

	myname = raw_input("What is your user name (max 8 characters)? ")

	app = MessageBoardController(myname, args.host, args.port, args.retries, args.timeout)
	app.run()




