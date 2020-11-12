#!/usr/bin/env python
'''
MAVSH module

details coming later
'''

import os
import os.path
import sys
import errno
import time
from pymavlink import mavutil
from pymavlink.dialects.v20 import ardupilotmega as mavlink
from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_util
from MAVProxy.modules.lib import mp_settings

#MAVSH_STATUS Enum values 
MAVSH_IDLE = mavlink.MAVSH_IDLE
#MAVSH_ACTIVE = mavlink.MAVSH_ACTIVE

#MAVSH_INIT_FLAG Enum values
MAVSH_SESSION_INIT = mavlink.MAVSH_SESSION_INIT
MAVSH_SESSION_ACCEPTED = mavlink.MAVSH_SESSION_ACCEPTED
MAVSH_SESSION_REJECTED = mavlink.MAVSH_SESSION_REJECTED
MAVSH_SESSION_EXIT = mavlink.MAVSH_SESSION_EXIT

class mavsh(mp_module.MPModule):
    def __init__(self, mpstate):
        """Initialise module"""
        super(mavsh, self).__init__(mpstate, "mavsh", "")
        self.mavsh_status = MAVSH_IDLE
        
        self.packets_mytarget = 0
        self.packets_othertarget = 0

        self.mavsh_settings = mp_settings.MPSettings([ ('verbose', bool, True),])
        self.add_command('mavsh', self.cmd_mavsh, "mavsh module", ['status','set (LOGSETTING)','start'])

    def usage(self):
        '''show help on command line options'''
        return "Usage: mavsh <status | set | start>"
    
    def cmd_mavsh(self, args):
        '''control behaviour of the module'''
        if len(args) == 0:
            print(self.usage())
        elif args[0] == "status":
            print(self.status())
        elif args[0] == "set":
            self.mavsh_settings.command(args[1:])
        elif args[0] == 'start':
            print(self.master.mav)
            self.mavsh_init()        
        else:
            print(self.usage())

    def status(self):
        '''returns information about module'''
        return ":lolulmfao:"
            


    def mavsh_init(self):
        '''
        need to take into account the system and component ID's of each device

        MUST be set in the parameters we're going to be using
    
        PARAMS:
            system_id = 1 as its the flight controller and we want to init the comm over that
            mavsh_uart = uart_connection # for the telemetry shell to be sent over
            gcs = id of the gcs used for the communications (should be 255?) 
                - if not 255 then send a rejection packet
        '''


        '''initializes mavsh link'''
        # send a mavsh_session_init packet        
        print(self.packets_mytarget)
        #actually prints a message!!!!
        print(self.master.mav.mavsh_init_encode(self.target_system,MAVSH_SESSION_INIT))
        self.master.mav.mavsh_init_send(self.target_system,MAVSH_SESSION_INIT)
        return 

    
    '''
    need to mofidy the vehicle code to respond to a session INIT with a session ACK

    the pi's version of the script needs to start like this
    - if packet recv and type == MAVSH_INIT:
        respond with mavsh_ack (system_id = 1, component id = rpi's component target system = 255, target component id = 1)
    '''

    def mavlink_packet(self, m):
        '''handle mavlink packets'''
        if m.get_type() == 'HEARTBEAT':
            print(m.values)

        elif m.get_type == 'MAVSH_INIT':
            print(m)

        elif m.get_type() == 'MAVSH_ACK':
            if self.settings.target_system == 0 or self.settings.target_system == m.get_srcSystem():
                self.packets_mytarget += 1                                   
            else:
                self.packets_othertarget += 1
           

def init(mpstate):
    '''initialise module'''
    return mavsh(mpstate)

    
