#!/usr/bin/python

# To Do:
# Add ChangeLog
# Add User Messaging feature
# Add AIML chat functionality
# docopt - Allow command line options to override default settings file or specific options
# Add optional password login for registered IRC nicks
# !help - List commands and options
# !weather - Houston 5 day weather forecast
# !events - List upcoming HAHA nights and any other notable events (BBQ?)
# !remind - Set a reminder
# !links - Show the last X links posted in chat to catch up on missed items
import logging
import os
import re
import socket
import urllib2
import settings


class JokerBot:
    def __init__(self):
        logging.basicConfig(filename=settings.LOG_FILE, level=logging.INFO)
        logging.info("Initializing " + settings.IRC_NICK)
        self.irc_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.irc_connection.connect((settings.IRC_HOST, settings.IRC_PORT))

        self.irc_connection.send("USER " + settings.IRC_NICK + " " + settings.IRC_NICK + " " + settings.IRC_NICK + " " + settings.IRC_NICK + "\n")
        self.irc_connection.send("NICK " + settings.IRC_NICK + "\n")
        self.irc_connection.send("JOIN " + settings.IRC_CHAN + "\n")

    def send_channel_message(self, msg):
        self.irc_connection.send("PRIVMSG " + settings.IRC_CHAN + " :" + msg + "\n")

    def get_names_from_channel(self):
        self.irc_connection.send("NAMES " + settings.IRC_CHAN + "\n")
        names_msg = self.irc_connection.recv(2048).strip()
        logging.info("Users in " + settings.IRC_CHAN + ": " + names_msg)
        names = names_msg.split(':', 2)[2]
        names = names.replace('\r', '')
        names = names.replace('\n', '')
        names = names.replace('@', '')
        names = names.replace('+', '')
        return names.split(' ')

    def search_mailbox(self, user):
        if not os.path.exists(settings.MAILBOX_FILE):
            # If there is no mailbox file, there's nothing to search through
            return
        mailbox = open(settings.MAILBOX_FILE, 'r')
        messages = mailbox.readlines()
        mailbox.close()
        for message in messages:
            mailbox_to, mailbox_msg = message.split(":::", 1)
            mailbox_msg.replace('\n', '')
            if mailbox_to.lower() == user.lower():
                logging.info("Message found for " + mailbox_to)
                self.send_channel_message(mailbox_to + ": " + mailbox_msg)
                mailbox = open(settings.MAILBOX_FILE, 'r+')
                lines = mailbox.readlines()
                mailbox.truncate(0)
                mailbox.seek(0)
                for line in lines:
                    if not line == message:
                        mailbox.write(line)
                mailbox.close()

    def add_message_queue(self, msg_to, msg):
        if not os.path.exists(settings.MAILBOX_FILE):  # Ensure the mailbox file exists
            open(settings.MAILBOX_FILE, 'w').close()
        mailbox = open(settings.MAILBOX_FILE, 'a+')
        mailbox.write(msg_to + ":::" + msg + "\n")
        mailbox.close()
        logging.info("Added to message queue")

    def start(self):
        while True:
            msg = self.irc_connection.recv(2048)
            msg_lower = msg.lower()

            # Respond to IRC ping
            if msg.find("PING") != -1:
                msg_text = msg.split()[1]
                self.irc_connection.send("PONG " + msg_text + "\n")
                continue

            # Respond to message pings
            if msg_lower.find(":!ping") != -1:
                msg_header, msg_text = msg.split(":!ping")
                self.send_channel_message('pong' + msg_text)

            # Respond to mentions - to Remove
            if msg_lower.find(settings.IRC_MENTION.lower()) != -1:
                msg_header, msg_text = msg.split(settings.IRC_MENTION)
                greetings = ["hi", "hello"]
                if any(a in msg_text.lower() for a in greetings):
                    self.send_channel_message(':Hello!')

            # Parse links mentioned in channel
            # TODO ignore the MOTD link
            if msg_lower.find(settings.IRC_CHAN.lower()) != -1:
                url = re.search(r'((http|https)://.*)', msg, re.I)
                if url:
                    url = url.group()
                    opener = urllib2.build_opener()
                    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                    try:
                        website_response = opener.open(url).read()
                    except Exception as e:
                        logging.warning('<' + url + '>: ' + str(e))
                    else:
                        website_title = re.search(r'<title.*?>(.*?)</title>', website_response, re.I | re.M | re.S)
                        if website_title:
                            website_title = website_title.group(1)
                            website_title = website_title.replace("\n", "")
                            website_title = website_title.replace("\r", "")
                            website_title = website_title.replace("\t", " ")
                            website_title = website_title.strip()
                            self.send_channel_message('[' + website_title + ']')

            # User messaging functionality
            if msg_lower.find(":!tell") != -1:
                msg_header, msg_text = msg.split(":!tell")
                sender = msg_header.split('!')[0][1:]
                msg_text = msg_text.strip()
                if ' ' in msg_text:
                    recipient, msg_text = msg_text.split(' ', 1)
                    msg_text = sender + ' says "' + msg_text + '"'
                    name_exists = 0
                    for name in self.get_names_from_channel():
                        if name.lower() == recipient.lower():
                            name_exists = 1
                            self.send_channel_message(
                                sender + ": " + recipient + " is already in this channel. No need for me to pass the message along. :)")
                            break
                    if not name_exists:
                        self.add_message_queue(recipient, msg_text)
                        self.send_channel_message(sender + ": I will relay the message to " + recipient + " when they get back.")
                else:
                    self.send_channel_message(sender + ": You need to supply a message.")

            if msg_lower.find(" join " + settings.IRC_CHAN.lower()) != -1:
                if msg_lower.find(" privmsg " + settings.IRC_CHAN.lower()) == -1:
                    new_user = msg.split('!')[0][1:]
                    logging.info("Searching mailbox for messages for " + new_user)
                    self.search_mailbox(new_user)


# If this script is run directly, start up the bot with the command line options or settings from the settings file
if __name__ == '__main__':
    bot = JokerBot()
    bot.start()
