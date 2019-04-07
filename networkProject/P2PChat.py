#!/usr/bin/python3

# Student name and No.: Tse Yik Ho, 3035441057
# Student name and No.: Wang Zehao, 3035331642
# Development platform: mac os
# Python version: 3
# Version: 1


from tkinter import *
import sys
import struct
import socket
import time
import threading
#
# Global variables
#
global name
global chatroomName

#
# This is the hash function for generating a unique
# Hash ID for each peer.
# Source: http://www.cse.yorku.ca/~oz/hash.html
#
# Concatenate the peer's username, str(IP address), 
# and str(Port) to form a string that be the input 
# to this hash function
#
def sdbm_hash(instr):
	hash = 0
	for c in instr:
		hash = int(ord(c)) + (hash << 6) + (hash << 16) - hash
	return hash & 0xffffffffffffffff

#
# Functions to handle user input
#
def do_User():
	# name is the variable to store the user's registered name
	global name, joined
	# checkName is a function to check whether the name satisfy the naming rules (eg. do not contains colon).
	if(checkName(userentry.get()) and (joined == False)):	
		#
		# System will not response to user button unless user enters a name
		# 
		name = userentry.get()
		outstr = "\nYou have changed your name to: " + name
		CmdWin.insert(1.0, outstr)
		userentry.delete(0, END)
	elif joined:
		outstr = "\nYou can not change your name after joining a room"
		CmdWin.insert(1.0, outstr)
		userentry.delete(0, END)

def do_List():
	add,port = sockfd.getpeername()
	CmdWin.insert(1.0, "\nConnected to server at %s::%d"%(add,port))
	message_format = struct.Struct('5s')
	msg = message_format.pack(b"L::\r\n")
	#
	# send bytes in format of string length of 5
	#
	sockfd.send(msg)
	rmsg = sockfd.recv(1000)
	#
	# receive bytes with unknown format length, so decode directly
	# 
	# test cases:
	# rmsg = b"G::\r\n"
	# rmsg = b"G:c3230:c3250:c3234::\r\n"
	# rmsg = b"G:c3230:c3250:c3234::\r:\n"
	# rmsg = b"F:there is no such error:\r\n"
	#
	print("The received message (raw):", rmsg)
	msg = rmsg.decode()
	#
	# decode into string and split message into a list:
	# [Head, room1, room2, room3, ..., room n, '', '\r\n']
	#
	rmsg_list = msg.split(':')
	print(rmsg_list)
	if (rmsg_list[-1] != '\r\n') or (rmsg_list[0] not in ('G','F')):
		#
		# if the list doesn't comply with certain protocol
		#
		print("unknown message received")
		CmdWin.insert(1.0, "\nunknown message received, please try again")
		# unknow message
	elif rmsg_list[0] == 'F':
		#
		# if the list returns failure error
		#
		print("server failed to get list due to an error")
		CmdWin.insert(1.0, "\nserver failed to get list due to an error:%s"%rmsg_list[1])
	elif len(rmsg_list) == 3:
		#
		# if the list is [G, '', '\r\n']
		#
		print("communication succeed")
		CmdWin.insert(1.0, "\nNo active chatrooms")
		# if server sent back a message length equal to 3, it mean connection success but currently no active room.		
	else:
		#
		# list carries room message
		#
		print("communication succeed")
		#
		# generate output to command window
		#
		outstr=""
		for i in range(1,len(rmsg_list)-2):
			outstr = "\n\t"+rmsg_list[i] + outstr
		outstr= "\nHere are the active chatrooms:" + outstr
		CmdWin.insert(1.0,outstr)
		# output the active chatrooms.

def do_Join():
	try:
		print("Join with the identity: %s and connection: %s::%d"%(name,sockfd.getsockname()[0],sockfd.getsockname()[1]))
	except NameError:
		#
		# if name is not yet defined, name error will occur:
		# generate corresponding output in command window
		# 
		CmdWin.insert(1.0,"\nPlease set your username first")
	else:
		if(checkRoomName(userentry.get())):
			#
			# System will not response to join button unless user enters roomname
			# 
			global room_name	
			room_name = userentry.get()
			msg = "J:%s:%s:%s:%d::\r\n"%(room_name,name,sockfd.getsockname()[0],sockfd.getsockname()[1])
			#
			# message has been generated
			# 
			messageLength = len(msg)
			print("Message Length: " + str(messageLength))
			message_format = struct.Struct(str(messageLength)+'s')
			#
			# produce corresponding packing method
			# 
			smsg = message_format.pack(msg.encode())
			userentry.delete(0, END)
			print("send first message")
			sockfd.send(smsg)
			rmsg = sockfd.recv(1000)
			print("received raw message:", rmsg)
			#
			# directly decode into string
			#
			msg = rmsg.decode()
			rmsg_list = msg.split(':')
			#
			# split into a list:
			# [Head, hashedValue, userName1, address1, portNumber1, 
			# 					  userName2, address2, portNumber2,
			#                     userName3, address3, portNumber3, '', '\r\n']
			#
			if (rmsg_list[-1] != '\r\n') or (rmsg_list[0] not in ('M','F')):
				#
				# if the list doesn't comply with certain protocol
				#
				print("unknown message received")
				CmdWin.insert(1.0, "\nunknown message received, please try again")
				# print out unknown message received   
			elif rmsg_list[0] == 'F':
				#
				# if the list returns failure error
				#
				print("server failed to get member due to an error")
				CmdWin.insert(1.0, "\nserver failed to get member due to an error:%s"%rmsg_list[1])
				# printout server failed to get member
			else:
				#
				# list carries member message
				#
				print("enter room succeed")
				#
				# below variables enters thread iteration:
				# 	room_list: to be updated every 20 seconds
				# 	iter_msg: a stable string to send to sever every 20 seconds
				#
				global room_list
				# variable to store the updated room_list.
				room_list = rmsg_list
				iter_msg = smsg
				#
				# generate output to command window
				# 
				outstr = ""
				for i in range(2,len(rmsg_list)-2,3):
					outstr = "\n\t"+rmsg_list[i] + outstr
				outstr ="\nnew member list updated: "+outstr
				CmdWin.insert(1.0, outstr)
				#
				# create a thread calling the keepAlive function with variable iter_msg as input
				# 
				global joined
				joined = True
				threading._start_new_thread(keepAlive,(iter_msg,))

def do_Send():
	CmdWin.insert(1.0, "\nPress Send")
	print(room_list)


def do_Poke():
	# 
	# check if user connected to a chatroom network. If no, point out the error message.
	# 
	if (joined):
		# 
		#  checkMemberName() handle whether the input field's name is in the group. If no, point out the error message.
		# 
		if(checkMemberName(userentry.get())):
			user_name = userentry.get()
			sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
			global room_name
			global name
			message = "K:"+room_name+":"+name+"::\r\n"			
			temp = room_list.index(user_name)
			new_sockAdd = (room_list[temp+1],int(room_list[temp+2]))
			sock.sendto(message.encode(), new_sockAdd)
			CmdWin.insert(1.0,"\nHave sent a poke to " + user_name)
			data = sock.recvfrom(2048)
			# if poke the user successfully
			#
			# directly decode into string
			#
			msg = data[0].decode()
			rmsg_list = msg.split(':')
			print(rmsg_list)
			# 
			# if received ACK successfully, print out the received ACK message.
			# 
			if (rmsg_list[-1] == '\r\n') and (rmsg_list[0] == 'A'):
				CmdWin.insert(1.0,"\nReceived ACK from " + userentry.get())
			else:
				# 
				# if did't received ACK message successfully, wait for 2 second then check again.
				# if still cannot get the message, print out the error message to user.
				# 
				time.sleep(2)
				if (rmsg_list[-1] == '\r\n') and (rmsg_list[0] == 'A'):
					CmdWin.insert(1.0,"\nReceived ACK from " + userentry.get())
				else:
					CmdWin.insert(1.0,"\nDid not received ACK from  " + userentry.get() + " because some problem occur.")

	else:
		CmdWin.insert(1.0,"\nYou connot poke anyone because you didn't join any group.")		

def do_Quit():
	CmdWin.insert(1.0, "\nPress Quit")
	sys.exit(0)

#
# My defined-Functions
#
def udpServer(dmp):
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)	
	sock.bind(sockfd.getsockname())
	while True:
		data, address = sock.recvfrom(2048)
		print("UDP received raw message:", data)
		#
		# directly decode into string
		#
		msg = data.decode()
		rmsg_list = msg.split(':')

		print(rmsg_list)
		if (rmsg_list[-1] == '\r\n') and (rmsg_list[0] == 'K'):
			ackMessage = "A::\r\n"	
			sock.sendto(ackMessage.encode(), address)
			outstr = "\n~~~~["+rmsg_list[2]+"]Poke~~~~"
			MsgWin.insert(1.0, outstr)
			outstr = "\nReceived a poke from "+rmsg_list[2]
			CmdWin.insert(1.0, outstr)


def keepAlive(msg):
	#
	# a function executed by thread after user enters a room successfully
	# 
	threading._start_new_thread(udpServer,(msg,))	
	while True:
		time.sleep(20)
		#
		# after 20 seconds thread sleeping
		# 
		print("send message to keep alive")
		sockfd.send(msg)
		rmsg = sockfd.recv(1000)
		print("received raw message:", rmsg)
		dmsg = rmsg.decode()
		#
		# directly decode into string
		#
		rmsg_list = dmsg.split(':')
		#
		# split into a list:
		# [Head, hashedValue, userName1, address1, portNumber1, 
		# 					  userName2, address2, portNumber2,
		#                     userName3, address3, portNumber3, '', '\r\n']
		#
		if (rmsg_list[-1] != '\r\n') or (rmsg_list[0] not in ('M','F')):
			#
			# if the list doesn't comply with certain protocol
			#
			print("unknown message received")
			CmdWin.insert(1.0, "\nunknown message received, please try again")
		elif rmsg_list[0] == 'F':
			#
			# if the list returns failure error
			#
			print("server failed to get member due to an error")
			CmdWin.insert(1.0, "\nserver failed to get member due to an error:%s"%rmsg_list[1])
		else:
			global room_list
			if room_list != rmsg_list:
				#
				# receive a list different from the previous one 
				# need inform the user in command window and update the global list for future actions
				# 
				outstr = ""
				for i in range(2,len(rmsg_list)-2,3):
					outstr = "\n"+rmsg_list[i] + outstr
				outstr ="\nnew member list updated: "+outstr
				CmdWin.insert(1.0, outstr)
				room_list = rmsg_list

#def isNameInGroupList(gpName):
#	for x in groupList:
#		if(x==gpName):
#			return True
#	return False
def isNameInGroupMemberList(name):
	return True

def isNameInGroupList(name):
	global room_list
	if name in room_list:
		return True
	return False

#def printGroupList(groupList):
#	for x in groupList:
#		print(x)

def getGroupMembers():
	return "tom"

def checkName(name):
	if (len(name) > 32 or len(name) < 1):
		global outstr
		outstr = "\nsorry, the length of username should be 1 - 32"
		CmdWin.insert(1.0, outstr)
		userentry.delete(0, END)
		return False
	if (containColon(name)):
		outstr = "\nsorry, username cannot contain symbol :"
		CmdWin.insert(1.0, outstr)
		userentry.delete(0, END)
		return False
	return True

def checkRoomName(name):
	if (len(name) > 32 or len(name) < 1):
		global outstr
		outstr = "\nsorry, the length of roomname should be 1 - 32"
		CmdWin.insert(1.0, outstr)
		userentry.delete(0, END)
		return False
	if (containColon(name)):
		outstr = "\nsorry, roomname cannot contain symbol :"
		CmdWin.insert(1.0, outstr)
		userentry.delete(0, END)
		return False
	return True

def checkMemberName(name):
	if (not name):		
		global outstr
		global room_list
		for i in range(2,len(room_list)-2,3):
			outstr = "\t"+room_list[i] + outstr
		outstr ="\nTo whom you want to send the poke? \n"+outstr
		CmdWin.insert(1.0, outstr)
		return False
	if (len(name) > 32 or len(name) < 1):		
		outstr = "\nsorry, the length of member name should be 1 - 32"
		CmdWin.insert(1.0, outstr)
		userentry.delete(0, END)
		return False
	if (containColon(name)):
		outstr = "\nsorry, member name cannot contain symbol :"
		CmdWin.insert(1.0, outstr)
		userentry.delete(0, END)
		return False
	if (not isNameInGroupList(name)):
		outstr = "\nsorry, member is not in the room."
		CmdWin.insert(1.0, outstr)
		userentry.delete(0, END)
		return False
	return True

def containColon(subject):
	for x in subject:
		if(x == ':'):
			return True
	return False

#
# Set up of Basic UI
#
win = Tk()
win.title("MyP2PChat")

#Top Frame for Message display
topframe = Frame(win, relief=RAISED, borderwidth=1)
topframe.pack(fill=BOTH, expand=True)
topscroll = Scrollbar(topframe)
MsgWin = Text(topframe, height='15', padx=5, pady=5, fg="red", exportselection=0, insertofftime=0)
MsgWin.pack(side=LEFT, fill=BOTH, expand=True)
topscroll.pack(side=RIGHT, fill=Y, expand=True)
MsgWin.config(yscrollcommand=topscroll.set)
topscroll.config(command=MsgWin.yview)

#Top Middle Frame for buttons
topmidframe = Frame(win, relief=RAISED, borderwidth=1)
topmidframe.pack(fill=X, expand=True)
Butt01 = Button(topmidframe, width='6', relief=RAISED, text="User", command=do_User)
Butt01.pack(side=LEFT, padx=8, pady=8);
Butt02 = Button(topmidframe, width='6', relief=RAISED, text="List", command=do_List)
Butt02.pack(side=LEFT, padx=8, pady=8);
Butt03 = Button(topmidframe, width='6', relief=RAISED, text="Join", command=do_Join)
Butt03.pack(side=LEFT, padx=8, pady=8);
Butt04 = Button(topmidframe, width='6', relief=RAISED, text="Send", command=do_Send)
Butt04.pack(side=LEFT, padx=8, pady=8);
Butt06 = Button(topmidframe, width='6', relief=RAISED, text="Poke", command=do_Poke)
Butt06.pack(side=LEFT, padx=8, pady=8);
Butt05 = Button(topmidframe, width='6', relief=RAISED, text="Quit", command=do_Quit)
Butt05.pack(side=LEFT, padx=8, pady=8);

#Lower Middle Frame for User input
lowmidframe = Frame(win, relief=RAISED, borderwidth=1)
lowmidframe.pack(fill=X, expand=True)
userentry = Entry(lowmidframe, fg="blue")
userentry.pack(fill=X, padx=4, pady=4, expand=True)

#Bottom Frame for displaying action info
bottframe = Frame(win, relief=RAISED, borderwidth=1)
bottframe.pack(fill=BOTH, expand=True)
bottscroll = Scrollbar(bottframe)
CmdWin = Text(bottframe, height='15', padx=5, pady=5, exportselection=0, insertofftime=0)
CmdWin.pack(side=LEFT, fill=BOTH, expand=True)
bottscroll.pack(side=RIGHT, fill=Y, expand=True)
CmdWin.config(yscrollcommand=bottscroll.set)
bottscroll.config(command=CmdWin.yview)

def main():
	if len(sys.argv) != 4:
		print("P2PChat.py <server address> <server port no.> <my port no.>")
		sys.exit(2)
	global sockfd, joined
	joined = False
	try:
		sockfd = socket.socket()
		sockfd.connect((sys.argv[1], int(sys.argv[2])))
	except socket.error as emsg:
		print("Socket error: ", emsg)
		sys.exit(1)
	win.mainloop()

if __name__ == "__main__":
	main()
# server ip address, server port number. my port number
