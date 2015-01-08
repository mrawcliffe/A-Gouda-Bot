import os, sys

sys.path.insert(0, 'modules/')

import socket
import importlib
import random

from init import ConfLoad
from net import NetLoad
from mods import ModLoad

import core
import loader

class CBot():
    def __init__(self):
        self.confpath = "conf/"
        self.libpath = "./"
        # load information from config file(s)
        self.configure()
        # actual irc connection
        nl = NetLoad(self.network, self.port, self.nick, self.chan)
        # all communication to server is done via self.irc
        self.irc = nl.conn()
        # module loader
        self.ml = ModLoad(self.libpath)
        # load all modules by default
        self.ml.mod_load_all()

    def in_list(self, ls, scmp):
        """ helper function for the quit command, might change later """
        for x in range(len(ls)):
            if scmp == ls[x]:
                return True
        return False

    def configure(self):
        """ load configuration info from settings file """
        self.conf = ConfLoad(self.confpath+"settings.ini")
        self.nick = self.conf.get_nick()
        self.network = self.conf.get_netw()
        self.port = self.conf.get_port()
        self.chan = self.conf.get_chan()
        self.admins = self.conf.get_admins()

    def loading_handler(self, arg, c):
        """ loading, unloading, reloading modules """
        cargs = []
        for x in range(5, len(arg)):
            # cargs contains all words after the command
            cargs.append(arg[x])
        for arg in loader.get_args():
            if c == arg:
                self.irc.send('PRIVMSG ' + self.chan + ' :' + getattr(loader, arg)(cargs[0], self.ml) + '\r\n')

    def quit(self, command, nick):
        self.irc.send('QUIT :Bye then...\r\n')
        exit()

    def list_commands(self, command):
        clist = "Current available commands: "
        if len(self.ml.get_args()) == 0:
            clist = "No available commands.  "
        else:
            for a in self.ml.get_args():
                clist = clist + a + ", "
        self.irc.send('PRIVMSG ' + self.chan + ' :' + clist[:-2] + '\r\n')

    def explicit_commands(self, arg, nick):
        """ commands """
        # user has not written anything
        if len(arg) <= 4:
            command = "null"
        else:
            command = arg[4]
            # should modules be loaded/reloaded/unloaded
            self.loading_handler(arg, command)
        """ quit command """
        if command == 'gtfo' and self.in_list(self.admins, nick):
            self.quit(command, nick)
        """ list all loaded modules """
        if command == 'modules':
            loaded_modules = ', '.join(list(set(self.ml.get_args().values())))
            self.irc.send('PRIVMSG ' + self.chan + ' :Loaded modules: '+loaded_modules+'\r\n')
        """ command to list all available commands """
        if command == 'cmds':
            self.list_commands(command)
        if command not in self.ml.get_args() and arg[len(arg)-1][len(arg[len(arg)-1])-1] == '?':
            if any("," in c for c in arg[4:len(arg)-1]):
                # maybe asking to choose?
                choice = core.choose(' '.join(arg[4:len(arg)]))
                self.irc.send('PRIVMSG ' + self.chan + ' :'+choice[random.randint(0, len(choice)-1)]+'\r\n')
            else:
                self.irc.send('PRIVMSG ' + self.chan + ' :Generic response...\r\n')
        """ parsing args corresponding to a module """
        for arg in self.ml.get_args():
            if command == arg:
                output = self.ml.get_arg(arg)
                self.irc.send('PRIVMSG ' + self.chan + ' :' + output + '\r\n')

    def passive_commands(self, arg, nick):
        """ this function will parse every line """
        prep = ["do", "should", "will", "can", "does", "are", "is", "if", "shall", "could", "was"]
        if arg[len(arg)-1][len(arg[len(arg)-1])-1] == '?' and arg[3][1:].lower() in prep:
            yn_table = ["yes", "no"]
            yn_response = yn_table[random.randint(0, 1)]
            self.irc.send('PRIVMSG ' + self.chan + ' :'+yn_response+'\r\n')

    def pong(self, data):
        if data.find('PING') != -1:
            self.irc.send('PONG ' + data.split()[1] + '\r\n')

    def run(self):
        print "Starting Gouda Bot"
        while True:
            data = self.irc.recv(4096)
            self.pong(data)
            if data.find('PRIVMSG') != -1:
                # get the nick of whoever sent the message
                user_nick = data.split('!')[0].replace(':', '')
                # get what they wrote
                message = ':'.join(data.split(':')[2:])
                # first word in a users message
                addressed_to = message.split()[0]
                arg = data.split()
                if addressed_to == self.nick+':':
                    self.explicit_commands(arg, user_nick)
                else:
                    if len(arg) >= 4:
                        self.passive_commands(arg, user_nick)

if __name__ == '__main__':
    bot = CBot()
    bot.run()
