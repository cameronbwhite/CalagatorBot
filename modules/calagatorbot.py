#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright (C) 2013, Cameron White

import logging
import feedparser
from kitnirc.modular import Module
from botparse import BotParse
import datetime
from itertools import takewhile
import re
 
_log = logging.getLogger(__name__)

parser = BotParse()
command_today = parser.add_command('!today')
command_today.add_argument('--limit', type=int)
command_tomorrow = parser.add_command('!tomorrow')
command_tomorrow.add_argument('--limit', type=int)

class CalagatorBot(Module):
    
    @Module.handle("PRIVMSG")
    def messages(self, client, actor, recipient, message):
    
        self.client = client
        self.actor = actor
        self.recipient = recipient
        self.message = message

        config = self.controller.config

        # Only pay attention if addressed directly in channels
        try:
            self.args = parser.parse_args(self.message.split())
        except (NameError, TypeError):
            _log.debug("message not reconized %r", self.message)
            return

        # Log a message to the INFO log level - see here for more details:
        # http://docs.python.org/2/library/logging.html
        _log.info("Responding to %r in %r", self.actor, self.recipient)
        
        if self.args.command == "!today":

            if self.args.help:
                messages = command_today.format_help().split('\n')
            else:
                def today_sort(entries):
                    entries = list(takewhile(
                        lambda x: 
                            get_start_time(x).date() <= datetime.date.today(),
                        entries,
                    ))
                    entries = filter(
                        lambda x:
                            get_start_time(x).date() == datetime.date.today(),
                        entries,
                    )
                    return entries
                messages = self.get_event_messages(today_sort)
        elif self.args.command == "!tomorrow":

            if self.args.help:
                messages = command_today.format_help().split('\n')
            else:
                def tomorrow_sort(entries):
                    today = datetime.datetime.today().date()
                    tomorrow = today + datetime.timedelta(days=1)
                    entries = list(takewhile(
                        lambda x: 
                            get_start_time(x).date() <= tomorrow,
                        entries,
                    ))
                    entries = filter(
                        lambda x:
                            get_start_time(x).date() == tomorrow,
                        entries,
                    )
                    return entries
                messages = self.get_event_messages(tomorrow_sort)

        elif self.args.command == "!help":
            messages = parser.format_help().split('\n')
        
        # send messages
        for message in messages:
            self.client.reply(self.recipient, self.actor, message)

        # Stop any other modules from handling this message.
        return True

    def get_event_messages(self, func=None):

        config = self.controller.config

        if self.args.limit:
            limit = self.args.limit
        elif config.has_option("calagatorbot", "limit"):
            try:
                limit = int(config.get("calagatorbot", "limit"))
            except TypeError:
                limit = None
        else:
            limit = None

        feeds = feedparser.parse(
            'http://calagator.org/events.atom'
        )
        entries = feeds.entries

        if func:
            entries = func(entries)
        
        if entries and limit >= 0:
            entries = entries[:limit]

        messages = []
        for entry in entries:
            
            start_time = get_start_time(entry)
            end_time = get_end_time(entry)

            message = '{} - {:%a, %b %d} from {:%H:%M} to {:%H:%M} - {}'.format(
                entry.title,
                get_start_time(entry),
                get_start_time(entry),
                get_end_time(entry),
                entry.link,
            )

            messages.append(message)
        return messages

def get_start_time(entry):
    start_time = re.sub(r':[0-9][0-9]-[0-9][0-9]:[0-9][0-9]', '', entry.start_time)
    return datetime.datetime.strptime(
        start_time,
        r'%Y-%m-%dT%H:%M',
    )

def get_end_time(entry):
    end_time = re.sub(r':[0-9][0-9]-[0-9][0-9]:[0-9][0-9]', '', entry.end_time)
    return datetime.datetime.strptime(
        end_time,
        r'%Y-%m-%dT%H:%M',
    )
    
module = CalagatorBot
