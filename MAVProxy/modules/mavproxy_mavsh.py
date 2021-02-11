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
import pdb

#MAVSH_STATUS Enum values 
MAVSH_IDLE = mavlink.MAVSH_IDLE
MAVSH_ACTIVE = mavlink.MAVSH_ACTIVE

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
        self.heartbeat = False                        
        self.mavsh_settings = mp_settings.MPSettings([ ('verbose', bool, True),])
        self.add_command('mavsh', self.cmd_mavsh, "mavsh module", ['status','set (LOGSETTING)','start'])
                            
        # the gcs version needs a different target system from the companion computer version so well use these as companion id values
        self.shell_sysid = 1
        self.shell_compid = 200
         
        # and these will be the gcs values                 
        self.gcs_sysid = 255
        self.gcs_compid = 1 

        # can also possibly access the values from self.settings but this will give us problems when we launch multiple MAVProxy instances
        #self.shell_sysid = self.settings.target_system
        #self.shell_compid = self.settings.target_component
       
        

    def usage(self):
        '''show help on command line options'''
        return "Usage: mavsh <status|set|start>"


    def cmd_mavsh(self, args):
        '''control behaviour of the module'''
        if len(args) == 0:
            print(self.usage())
        elif args[0] == "status":
            print(self.status())
        elif args[0] == "set":
            self.mavsh_settings.command(args[1:])
        elif args[0] == 'start':
            print(self.master.mav) #<pymavlink.dialects.v20.ardupilotmega.MAVLink object at 0x7fe591e7d8e0>
            pdb.set_trace()
            print(self.target_system) #default is 1
            self.mavsh_init()        
        else:
            print(self.usage())

    
    def status(self):
        '''returns information about module'''
        return "lol"            


    def mavsh_init(self):
        '''
        need to take into account the system and component ID's of each device

        MUST be set in the parameters we're going to be using

        PARAMS:
            system_id = 1 as its the flight controller and we want to init the comm over that
            mavsh_uart = uart_connection # for the telemetry shell to be sent over
            gcs = id of the gcs used for the communications (should be 255?) 
                - if not 255 then send a rejection packet
        

        initializes mavsh link
        # send a mavsh_session_init packet        
        #print(self.packets_mytarget)
        #actually prints a message!!!!
        
        
        dictionary w/ all params 
        print(self.mav_param)
        
        these 2 statements are the same
        print(self.mav_param['SYSID_THISMAV'])
        print(self.target_system)
        
        SERIAL_CONTROL_DEV_TELEM1 is used for mavsh by default        
        '''        
        
        #currently need to have mavproxy turn on with a specific source sys and compid on the rpi for this to work -
        # mavlink router could probably fix the need for this 
        self.master.mav.mavsh_init_send(
            self.gcs_id,
            self.gcs_compid,
            self.shell_sysid,
            self.shell_compid,
            mavlink.MAVSH_SESSION_INIT
        )
        
        '''
        random tests
        
        #print(self.master.mav.mavsh_init_encode(self.target_system,MAVSH_SESSION_INIT))
        #self.master.mav.mavsh_init_send(self.target_system,MAVSH_SESSION_INIT)
        #print(self.master.mav.mavsh_ack_encode(self.target_system,MAVSH_SESSION_ACCEPTED))
        #self.master.mav.mavsh_ack_send(self.target_system,MAVSH_SESSION_ACCEPTED)
        #print('Component setup for routing in simulator without rpi is:')
        print(f"fc comp: {self.master.source_component} fc system: {self.master.source_system}")
        print(f"gcs comp: {self.master.target_component} gcs system: {self.master.target_system}")
        #print(mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL)
        #print(dir(self.master.mav))
        return 
        '''
    
    '''
    need to mofidy the vehicle/companion_computer code to respond to a session INIT with a session ACK
    
    the pi's version of the script needs to start like this
    - if packet recv and type == MAVSH_INIT:
        respond with mavsh_ack (system_id = 1, component id = rpi's component target system = 255, target component id = 1)
        
    '''

    def mavlink_packet(self, m):
        '''handle mavlink packets'''
        
        if m.get_type() == 'HEARTBEAT':            
            if self.heartbeat == True:
                pass
            else:                
                #print(dir(m))
                print(f"src_system: {m.get_srcSystem()} src_component: {m.get_srcComponent()}")                
                self.heartbeat = True
            
        elif m.get_type == 'MAVSH_INIT':
            
            # when INIT message is received we need to send an ack packet
            # dont toggle any status values until ack is received and synacked
            # this will work over udp but its behavior is slightly different over serial

            # check to verify that the packets came from the GCS were expecting them to come from
            # if a MAVSH_INIT came from any device which isnt the expected source system and source component then we reject the session
            print(m)
            if not (m.get_srcSystem() == self.gcs_sysid and m.get_srcComponent() == self.gcs_compid):
                self.master.mav.mavsh_ack_send(
                    self.shell_sysid, # sysid
                    self.shell_compid, # compid
                    self.gcs_sysid, # target system
                    self.gcs_compid, # target component
                    mavlink.MAVSH_SESSION_REJECTED # setup flag
                )
            
            # when the correct device initializes it we can accept the session
            # although I can imagine we have to check some more status flags and things
            else:                    
                if self.mavsh_status == mavlink.MAVSH_ACTIVE: 
                    print('mavsh already active')
                    return()

                self.master.mav.mavsh_ack_send(
                    self.shell_sysid, # sysid
                    self.shell_compid, # compid
                    self.gcs_sysid, # target system
                    self.gcs_compid, # target component
                    mavlink.MAVSH_SESSION_ACCEPTED # setup flag
                )
                
                

        elif m.get_type() == 'MAVSH_ACK':
            
            print(m)
            if self.target_system == 0:                
                '''
                need to test this with the gcs being bound and running this mavproxy instance
                once we receive this ack, we need to...? I forget I need to check the packet structure
                but we will have to toggle the status to active whenever we get here
                '''
                self.mavsh_status = MAVSH_ACTIVE
                 
               
                
def init(mpstate):
    '''initialise module'''
    return mavsh(mpstate)

    
