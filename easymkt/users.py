# -*- coding: utf-8 -*-
from base import MikrotikBase, MikrotikException, MikrotikConnectException
from basic_command import BasicCommand
from defines import *
import logging

class ModifyUser(MikrotikBase,BasicCommand):
    
    def __init__(self,action,act,devices,user,details,password=None,group=None):
        MikrotikBase.__init__(self)
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',datefmt='%m/%d/%Y %H:%M', filename=self.parameters['LOG_FILE'], level=eval(self.parameters['LOG_LEVEL']))
        self.action = action
        self.act = act
        self.devices = devices
        self.user = user
        self.password = password
        self.group = group
        self.details = details
        
    def main(self):
        ssh = self.prepaire_connect()

        if self.act == 'one' or self.act == 'all':
            mikrotiks = [['%s'%self.devices]] if self.devices else self.mikrotiks
        elif self.act == 'list':
            mikrotiks = self.parse_devices(self.devices)

        total = len(mikrotiks)

        for mikrotik in mikrotiks:
            try:
                addr = mikrotik[0]
                name = mikrotik[1] if len(mikrotik) >= 2 else None
                place = mikrotik[2] if len(mikrotik) >= 3 else None
            except KeyError,e:
                raise MikrotikException, "Device list error. Check device list format. Message: %s"%e

            """Default report parameters"""
            report = {
                      'addr':addr, 'name':name, 'location':place,
                      'file':None, 'status':None, 'error':None, 'clean':None,
                      'finally':None, 'class':None, 'dir':None
                      }

            try:
                userparam = {'user':self.user,'group':self.group,'pass':self.password}

                if self.action == 'newuser':
                    self.MikrotikNewUser(ssh,addr,self.parameters,userparam)
                elif self.action == 'usermod':
                    self.MikrotikModUser(ssh,addr,self.parameters,userparam)
                elif self.action == 'deluser':
                    self.MikrotikDelUser(ssh,addr,self.parameters,userparam)

            except MikrotikConnectException as msg:
                report['error'] = msg
                logging.warning(msg)
            except MikrotikException as msg:
                report['error'] = msg
                logging.error(msg)
            finally:
                report['status'] = STATUS_FAIL if report['error'] else STATUS_OK
                self.reports.append(report)

                # Output report to console
                self.view_report(self.details,report)

        """Send Report"""
        if self.details['mailreport']:
            self.send_report(self.action,total)
