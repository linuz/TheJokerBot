#!/usr/bin/python

#To Do:
# Add Help
# Add ChangeLog
# Add To Do
# Add User Messaging feature
# Lots of other things

import os
import re
import socket
import sys
import urllib2

IRC_HOST = "chat.freenode.net"
IRC_PORT = 6667
IRC_CHAN = "#HoustonHackers"
IRC_NICK = "TheJokerBot"
IRC_PASS = ""
IRC_MENT = ":" + IRC_NICK + ":"
MAILBOX_FILE = "mailbox.txt"

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

irc_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc_connection.connect((IRC_HOST, IRC_PORT))

irc_connection.send("USER " + IRC_NICK + " " + IRC_NICK + " " + IRC_NICK + " " + IRC_NICK + "\n")
irc_connection.send("NICK " + IRC_NICK + "\n")
irc_connection.send("JOIN " + IRC_CHAN + "\n")

if not os.path.exists(MAILBOX_FILE):
    open(MAILBOX_FILE, 'w').close() 

def sendChannelMessage(msg):
	irc_connection.send("PRIVMSG " + IRC_CHAN + " :" + msg + "\n")

def getNamesFromChannel():
	irc_connection.send("NAMES " + IRC_CHAN + "\n")
	names_msg = irc_connection.recv(2048)
	print names_msg
	names = names_msg.split(':', 2)[2]
	names = names.replace('\r', '')
	names = names.replace('\n', '')
	names = names.replace('@', '')
	names = names.replace('+', '')
	return names.split(' ')
	
def addMessageQueue(msg_to, msg):
	mailbox = open(MAILBOX_FILE, 'a+')
	mailbox.write(msg_to + ":::" + msg + "\n")
	mailbox.close()
	print "Added to message queue"
	
def searchMailbox(user):
	mailbox = open(MAILBOX_FILE, 'r')
	messages = mailbox.readlines()
	mailbox.close()
	for message in messages:
		mailbox_to, mailbox_msg = message.split(":::",1)
		mailbox_msg.replace('\n', '')
		if mailbox_to.lower() == user.lower():
			print "Message found for " + mailbox_to
			sendChannelMessage(mailbox_to + ": " + mailbox_msg)
			mailbox = open(MAILBOX_FILE, 'r+')
			lines = mailbox.readlines()
			mailbox.truncate(0)
			mailbox.seek(0)
			for line in lines:
				if not line == message:
					mailbox.write(line)
			mailbox.close()
		
while 1:
	msg_header = ""
	msg_text = ""
	msg = irc_connection.recv(2048)
	msgLower = msg.lower()
	
	# Respond to IRC ping
	if msg.find("PING") != -1:
		msg_text = msg.split()[1]
		irc_connection.send("PONG " + msg_text + "\n")
		continue
	else:
		print msg
	
	# Respond to message pings	
	if msgLower.find(":!ping") != -1:
		msg_header, msg_text = msg.split(":!ping")
		sendChannelMessage('pong' + msg_text)
		
	# Respond to mentions - to Remove
	if msgLower.find(IRC_MENT.lower()) != -1:
		msg_header, msg_text = msg.split(IRC_MENT)
		greetings = ["hi", "hello"]
		if any(a in msg_text.lower() for a in greetings):
			sendChannelMessage(':Hello!')
			
	# Parse links mentioned in channel
	if msgLower.find(IRC_CHAN.lower()) != -1:
		url = re.search(r'((http|https)://.*)', msg, re.I)
		if url:
			url = url.group()
			try:
				website_response = opener.open(url).read()
			except Exception as e:
				print '<' + url + '>: ' + str(e)
			else:
				website_title = re.search(r'<title.*?>(.*?)</title>', website_response, re.I|re.M|re.S)
				if website_title:
					website_title = website_title.group(1)
					website_title = website_title.replace("\n", "")
					website_title = website_title.replace("\r", "")
					website_title = website_title.replace("\t", " ")
					website_title = website_title.strip()
					sendChannelMessage('[' + website_title + ']')
	
	# User messaging functionality
	if msgLower.find(":!tell") != -1:
		msg_header, msg_text = msg.split(":!tell")
		msg_from = msg_header.split('!')[0][1:]
		msg_text = msg_text.strip()
		if ' ' in msg_text:
			msg_to, msg_text = msg_text.split(' ', 1)
			msg_text = msg_from + ' says "' + msg_text + '"'
			nameExists = 0
			for name in getNamesFromChannel():
				if name.lower() == msg_to.lower():
					nameExists = 1
					sendChannelMessage(msg_from + ": " + msg_to	+ " is already in this channel. No need for me to pass the message along. :)")
					break
			if not nameExists:
				addMessageQueue(msg_to, msg_text)
				sendChannelMessage(msg_from + ": I will relay the message to " + msg_to + " when they get back.")
		else:
			sendChannelMessage(msg_from + ": You need to supply a message.")
			
	if msgLower.find(" join " + IRC_CHAN.lower()) != -1:
		if msgLower.find(" privmsg " + IRC_CHAN.lower()) == -1: 
			new_user = msg.split('!')[0][1:]
			print "Searching mailbox for messages for " + new_user
			searchMailbox(new_user)