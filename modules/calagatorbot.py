#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Copyright (C) 2013, Cameron White

import logging
import feedparser
from kitnirc.modular import Module
import datetime
from itertools import takewhile, dropwhile
import re
 
_log = logging.getLogger(__name__)

weekdays = [
    'monday', 'tuesday', 'wednesday', 'thursday',
    'friday', 'saturday', 'sunday',
] 

class CalagatorBot(Module):
    
    @Module.handle("PRIVMSG")
    def messages(self, client, actor, recipient, message):
    
        self.client = client
        self.actor = actor
        self.recipient = recipient
        self.message = message

        config = self.controller.config

        message = message.split()
        
        if message[0] != '{}:'.format(self.client.user.nick):
            _log.debug("The message is not address to the bot")
            return True

        if len(message) >= 2:
            command = message[1].lower()
        else:
            _log.debug("The user did not enter a command")
            return True

        # Log a message to the INFO log level - see here for more details:
        # http://docs.python.org/2/library/logging.html
        _log.info("Responding to {} in {}".format(self.actor, self.recipient))
        
        if message[1] == "today":
            today = datetime.datetime.today().date()
            self.do_command(
                lambda x: filter_take_date(x, today)
            )
        elif message[1] == "tomorrow":
            today = datetime.datetime.today().date()
            tomorrow = today + datetime.timedelta(days=1)
            self.do_command(
                lambda x: filter_take_date(x, tomorrow)
            )

        elif message[1].lower() in weekdays:
            today = datetime.datetime.today().date()
            self.do_command(
                lambda x: filter_next_weekday(x, today, message[1])
            )
        else:
            _log.debug("{} is not a valid command".format(message[1]))
        
        # Stop any other modules from handling this message.
        return True

    def do_command(self, command=None):
        
        # If the config file/data can't be load then stop now.
        if not self.read_config():
            return

        feed = feedparser.parse(self.url)
        
        _log.debug("loaded {} entries".format(len(feed.entries)))  

        for entry in command(feed.entries):
            self.client.reply(
                self.recipient, 
                self.actor, 
                self.construct_message(entry)
            )

    def construct_message(self, entry):
        try: 
            start_time = get_start_time(entry)
            end_time = get_end_time(entry)
            link = getattr(entry, 'link', None)

            message = '{} - {:%a, %b %d} from {:%H:%M}'.format(
                entry.title,
                start_time,
                start_time,
            )
            if end_time:
                message += ' to {:%H:%M} '.format(end_time)
            if link:
                message += ' - {}'.format(link)
            
            _log.debug("message: {}".format(message))
            return message
        except Exception as e:
            _log.debug(e.strerror())

    def read_config(self):
        config = self.controller.config

        if not config.has_section("calagatorbot"):
            _log.error("config has no `calagatorbot` section")
            return False

        if config.has_option("calagatorbot", "url"):
            self.url = config.get("calagatorbot", "url")
        else:
            _log.error("config `calagatorbot` section has no `url` option")
            return False

        return True

def filter_take_date_range(events, start_date, end_date):
    """ Events filter which takes events which dates in the range
    from start_date to end_date inclusively. start_date >= end_date.
    events must be a list of the form [(id, event)]. """
   
    if start_date:
        events = dropwhile(
            lambda x: get_start_time(x).date() < start_date,
            events
        )

    if end_date:
        events = takewhile(
            lambda x: get_start_time(x).date() <= end_date,
            events
        )

    return events

def filter_take_date(events, date):
    return filter_take_date_range(events, date, date)

def filter_next_weekday(events, start_date, weekday):
    # The date to filter by will be constructed.

    # Get the int encoding of the day of the week.
    # Monday = 0 ... Sunday = 6
    start_date_weekday = start_date.weekday()
    
    days = weekday_difference(start_date_weekday, weekday)

    # Construct the date by adding the calculated number of
    # days.
    date = start_date + datetime.timedelta(days=days)
    return filter_take_date(events, date)

def weekday_difference(from_weekday, to_weekday):

    def get_weekday_index(weekday):
        if weekday not in range(7):
            weekday = weekdays.index(weekday.lower())
        return weekday
    
    from_weekday = get_weekday_index(from_weekday)
    to_weekday = get_weekday_index(to_weekday)

    if to_weekday >= from_weekday:
        # If from is Wednesday and Wednesday is to then
        # the day should not be changed.
        #     Wednesday - Wednesday = 2 - 2 = 0
        # If from is Tuesday and Friday is to then
        # the day should be increased by 3
        #     Friday - Tuesday = 4 - 1 = 3
        days = to_weekday - from_weekday
    else:
        # If from is Friday and Monday is to then the
        # day should be increased by 3.
        #    7 - Friday + Monday = 7 - 4 + 0 = 3 
        # If from is Thursday and Tuesday is to then the
        # day should be increased by 5.
        #    7 - Thursday + Tuesday = 7 - 3 + 1 = 5
        days = 7 - from_weekday + to_weekday

    return days
def get_start_time(entry):
    start_time = re.sub(r':[0-9][0-9]-[0-9][0-9]:[0-9][0-9]', '', entry.start_time)
    return datetime.datetime.strptime(
        start_time,
        r'%Y-%m-%dT%H:%M',
    )

def get_end_time(entry):
    try:
        end_time = re.sub(
            r':[0-9][0-9]-[0-9][0-9]:[0-9][0-9]', 
            '', entry.end_time)
        return datetime.datetime.strptime(
            end_time,
            r'%Y-%m-%dT%H:%M',
        )
    except AttributeError:
        return None
    
module = CalagatorBot
