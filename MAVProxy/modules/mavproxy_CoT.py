#!/usr/bin/env python
'''
CoT (Cursor on Target) Module
Brad Hards, July 2017
Based very heavily on Example module by Peter Barker, September 2016. Thanks for making that!

This module outputs CoT messages that correspond to the mavlink packet content.
'''

import os
import os.path
import sys
from pymavlink import mavutil
import errno
import time
import pycot
import datetime
import uuid
import socket

from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_util
from MAVProxy.modules.lib import mp_settings


class CoT(mp_module.MPModule):
    def __init__(self, mpstate):
        """Initialise module"""
        super(CoT, self).__init__(mpstate, "CoT", "")
        self.status_callcount = 0

        self.packets_mytarget = 0
        self.verbose = False

        self.CoT_settings = mp_settings.MPSettings(
            [ ('verbose', bool, False),
          ])
        self.add_command('CoT', self.cmd_CoT, "CoT module", ['status','set (LOGSETTING)'])

    def usage(self):
        '''show help on command line options'''
        return "Usage: CoT <status|set>"

    # TODO: this will need some kind of port setting
    def cmd_CoT(self, args):
        '''control behaviour of the module'''
        if len(args) == 0:
            print self.usage()
        elif args[0] == "status":
            print self.status()
        elif args[0] == "set":
            self.CoT_settings.command(args[1:])
        else:
            print self.usage()

    def status(self):
        '''returns information about module'''
        self.status_callcount += 1
        return("status called %(status_callcount)d times.  My target positions=%(packets_mytarget)u." %
               {"status_callcount": self.status_callcount,
                "packets_mytarget": self.packets_mytarget,
               })

    def mavlink_packet(self, m):
        '''handle mavlink packets'''
        if m.get_type() == 'SYSTEM_TIME':
            print "system_time"
            print m
        if m.get_type() == 'GLOBAL_POSITION_INT_COV':
            print "position cov"
            print m
        if m.get_type() == 'GLOBAL_POSITION_INT':
            if self.settings.target_system == 0 or self.settings.target_system == m.get_srcSystem():
                self.packets_mytarget += 1
                # print "Position: " + str(m.lat * 1.0e-7) + ", " + str(m.lon * 1.0e-7)
                pt = pycot.Point()
                pt.lat = m.lat * 1.0e-7
                pt.lon = m.lon * 1.0e-7
                pt.ce = 9999999
                pt.le = 9999999
                # TODO: convert to hae - this is really AMSL
                pt.hae = m.alt * 1.0e-3

                evt = pycot.Event()
                evt.point = pt
                evt.version = 2.0
                # find the right kind of CoT for a small UAV
                evt.event_type = 'a-f-A-B-C-x'
                # TODO: find some kind of permanent ID
                evt.uid = uuid.uuid4()
                # TODO: get time from packet?
                evt.time = datetime.datetime.utcnow()
                evt.how = 'm-f'

                # address = ("127.0.0.1", 18999)
                address = ("192.168.40.104", 18000)
                evt_bytes = evt.render(standalone=True)
                cot_int = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                cot_int.sendto(evt_bytes, address)

def init(mpstate):
    '''initialise module'''
    return CoT(mpstate)
