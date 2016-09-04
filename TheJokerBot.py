#!/usr/bin/python

#To Do:
# Add Help
# Add ChangeLog
# Add To Do
# Add User Messaging feature
# Lots of other things

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

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

irc_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc_connection.connect((IRC_HOST, IRC_PORT))
print "Connected to " + IRC_HOST + ":" + str(IRC_PORT)

irc_connection.send("USER " + IRC_NICK + " " + IRC_NICK + " " + IRC_NICK + " " + IRC_NICK + "\n")
irc_connection.send("NICK " + IRC_NICK + "\n")
irc_connection.send("JOIN " + IRC_CHAN + "\n")
print "Joined channel " + IRC_CHAN


while 1:
	msg_header = ""
	msg_text = ""
	#print "Header: " + msg_header
	#print "Text: " + msg_text
	msg = irc_connection.recv(2048)
	print msg
	
	# Respond to IRC ping
	if msg.find("PING") != -1:
		print "Responding to PING"
		msg_text = msg.split()[1]
		irc_connection.send("PONG " + msg_text + "\n")
	
	# Respond to message pings	
	if msg.find(":!ping") != -1:
		msg_header, msg_text = msg.split(":!ping")
		irc_connection.send("PRIVMSG " + IRC_CHAN + " :pong" + msg_text + "\n")
		
	# Respond to mentions - to Remove
	if msg.find(IRC_MENT) != -1:
		msg_header, msg_text = msg.split(IRC_MENT)
		greetings = ["hi", "hello"]
		if any(a in msg_text.lower() for a in greetings):
			irc_connection.send("PRIVMSG " + IRC_CHAN + " :Hello!" + "\n")
	
	# Parse links mentioned in channel
	if msg.find(IRC_CHAN) != -1:
		url = re.search(r'((http|https)://.*)', msg, re.I)
		if url:
			url = url.group()
			print "URL: " + url
			try:
				website_response = opener.open(url).read()
			except Exception as e:
				print "Problem with: " + url
				print e
			else:
				website_title = re.search(r'<title.*?>(.*?)</title>', website_response, re.I|re.M|re.S)
				if website_title:
					website_title = website_title.group(1)
					website_title = website_title.replace("\n", "")
					website_title = website_title.replace("\r", "")
					website_title = website_title.replace("\t", " ")
					website_title = website_title.strip()
					print "Title: " + website_title
					irc_connection.send("PRIVMSG " + IRC_CHAN + " :[" + website_title + "]\n")
				else:
					print "No title found for: " + url
				