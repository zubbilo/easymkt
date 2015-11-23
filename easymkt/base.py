#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, logging
from datetime import date
import re
import paramiko, socket
import scp
import smtplib
from defines import *
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
import ConfigParser
from time import sleep

class MikrotikBase(object):
        
    def __init__(self):
        self.version = date.today().strftime("%Y-%m-%d")
        self.parameters = self.parse_settings()
        if self.check_settings:
            self.mikrotiks = self.parse_devices()
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',datefmt='%m/%d/%Y %H:%M', filename=self.parameters['LOG_FILE'], level=eval(self.parameters['LOG_LEVEL']))
        """Needing data for send report"""
        self.summary = {'total':len(self.mikrotiks), 'success':0, 'fail':0}
        self.reports = []
        self.html = []
        return super(MikrotikBase, self).__init__()
    
    def view_report(self,details,report):
        """Output details to console or not"""
        if details['verbose']:
            print report
        else:
            if details['quite']:
                pass
            else:
                if report['error']:
                    print "%(addr)s -> %(name)s -> %(error)s"%report
                else:
                    print "%(addr)s -> %(name)s -> Success"%report
            
    def prepaire_connect(self):
        """Connect ssh to mikrotik"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        return ssh
            
    def parse_devices(self,file=None):
        """Return list of mikrotik devices from parameter DEVICE_LIST"""
        if not file: file = self.parameters['DEVICE_LIST']
        devices = []
        try:
            with open(file,'r') as f:
                for device in f:
                    devices.append(device.strip().split(';'))
        except IOError as e:
            logging.error('Couldn\'t read device list: %s.'%e)
            raise MikrotikSettingsException('Couldn\'t read device list: %s.'%e)
        else:
            return devices

    def parse_settings(self):
        """Return parameters dict from settings.py"""
        file = os.path.join(os.path.dirname(__file__), 'settings.cfg')
        
        # Initialization ConfigParser
        config = ConfigParser.RawConfigParser()

        # Check if config file exist
        if not os.path.isfile(file):
            raise MikrotikSettingsException, "Config file doesn't exist or not readable. Check for %s"%file

        # Read config file
        config.read(file)

        parameters = {}
        # Get general parameters
        try:
            parameters['BKP_DIR'] = config.get('general','bkp_dir')
            parameters['BKP_URL'] = config.get('general','bkp_url')
            parameters['DEVICE_LIST'] = config.get('general','device_list')
            parameters['AUTH_USER'] = config.get('general','auth_user')
            parameters['AUTH_PASS'] = config.get('general','auth_pass')
            parameters['TIMEOUT'] = config.get('general','timeout')
        except Exception,e:
            logging.error("Settings error, Message: %s"%e)
            raise MikrotikSettingsException, "Settings error when get general, Message: %s"%e  

        # Get debug parameters
        try:
            parameters['LOG_FILE'] = config.get('debug','log_file')
            parameters['LOG_LEVEL'] = config.get('debug','log_level')
            parameters['DEBUG_IN_NOTIFY'] = config.get('debug','debug_in_notify')
        except Exception,e:
            logging.error("Settings error, Message: %s"%e)
            raise MikrotikSettingsException, "Settings error when get debug, Message: %s"%e  

        # Get mail parameters
        try:
            parameters['MAIL_SERVER'] = config.get('mail','server')
            parameters['MAIL_FROM'] = config.get('mail','from')
            parameters['MAIL_TO'] = config.get('mail','to')
        except Exception,e:
            logging.error("Settings error, Message: %s"%e)
            raise MikrotikSettingsException, "Settings error when get mail, Message: %s"%e  

        return parameters
    
    def check_settings(self):
        """Checking settings parameters on errors and set default for non mandatory."""
        try:
            """ Check mandatory parameters exist """
            if not self.parameters['DEVICE_LIST']:
                raise MikrotikSettingsException('DEVICE_LIST is not readable.')
            if not self.parameters['AUTH_USER']:
                raise MikrotikSettingsException('AUTH_USER is not readable.')
            if not self.parameters['AUTH_PASS']:
                raise MikrotikSettingsException('AUTH_PASS is not readable.')
            
            """ Set default parameters """
            if not self.parameters['BKP_DIR']:
                self.parameters['BKP_DIR'] = '/tmp/'
            if not self.parameters['LOG_FILE']:
                self.parameters['LOG_FILE'] = '/tmp/easymkt.log'
            if not self.parameters['LOG_LEVEL']:
                self.parameters['LOG_LEVEL'] = logging.info
            if not self.parameters['TIMEOUT']:
                self.parameters['TIMEOUT'] = 5
            if not self.parameters['MAIL_FROM']:
                self.parameters['MAIL_FROM'] = 'mikrotik.backup@localhost'
            
            """ Check file and directory exist """
            if not os.path.exists(self.parameters['BKP_DIR']):
                raise MikrotikSettingsException('Backup dir doesn\'t exist!')
            if not os.path.isfile(self.parameters['DEVICE_LIST']):
                raise MikrotikSettingsException('Devices list doesn\'t exist!')

        except Exception,e:
            raise MikrotikSettingsException('Settings error: %s.'%e)
        else:
            return True

    def check_file_exist(self,name,dirname,type):
        dirbkp = self.parameters['BKP_DIR'] + dirname
        filebkp = dirbkp + "/" + name + type
        if not os.path.isdir(dirbkp):
            os.makedirs(dirbkp)
            return False
        if not os.path.isfile(filebkp): 
            return False
        elif os.path.getsize(filebkp)<1000:
	    os.remove(filebkp)
	    return False
        else:
            return True

    def send_report(self,func = None, total = None):
        """Prepaire output data"""
        
        if total:
            self.summary['total'] = total
        
        for r in self.reports:
            # set URL
            r['file'] = self.parameters['BKP_URL']%{'url':r['dir']} if (r['dir'] != "UNKNOWN") else 'unknown'
            # Cheat for not backup functions
            if r['finally'] == None:
                r['finally'] = FINALLY_OK
            # Check STATUS
            if r['status'] == STATUS_OK and r['finally'] == FINALLY_OK:
                r['status'] = "Success."
                r['class'] = CLASS_SUCCESS
                self.summary['success'] += 1
            elif r['status'] == STATUS_EXIST:
                r['status'] = "Actual."
                r['class'] = CLASS_SUCCESS
                self.summary['success'] += 1
            elif r['status'] == STATUS_FAIL or r['finally'] == FINALLY_FAIL:
                r['status'] = "FAIL!"
                r['class'] = CLASS_FAIL
                self.summary['fail'] += 1
            elif r['status'] == STATUS_OK:
                r['status'] = "Not get or clean!"
                r['class'] = CLASS_DEFAULT
                self.summary['fail'] += 1
            else:
                r['status'] = "Unknown"
                r['class'] = CLASS_DEFAULT
                self.summary['fail'] += 1

        """Use template"""
        tpl = Environment(loader=FileSystemLoader(os.path.dirname(__file__)), trim_blocks=True)
        self.html = tpl.get_template('mail_template.html').render( date = self.version, mikrotiks = self.reports, summary = self.summary, debug = self.parameters['DEBUG_IN_NOTIFY'], function = func)
        """SEND REPORT"""
        self.mailer(func)

    def mailer(self,subj):
        """Send mail notification"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Mikrotiks %s complete at %s"%(subj,self.version)
            msg['From'] = self.parameters['MAIL_FROM']
            msg['To'] = self.parameters['MAIL_TO']
            part = MIMEText(self.html, 'html')
            msg.attach(part)
            msg.preamble
            s = smtplib.SMTP(self.parameters['MAIL_SERVER'])
            s.sendmail(self.parameters['MAIL_FROM'], self.parameters['MAIL_TO'], msg.as_string()) # msg.as_string()
            s.quit()
        except Exception,e:
            logging.error("Send mail error: %s"%e)
        else:
            logging.info("Send notification successfull.")

"""END MikrotikBase"""

def connect_to_mikrotik(fn):
    """Decorator for connection to mikrotik"""
    def connect(self=None,ssh=None,addr=None,param=None,custom=None):
        try:
            ssh.connect(
                        addr,22,
                        param['AUTH_USER'],
                        param['AUTH_PASS'],
                        allow_agent=False,
                        look_for_keys=False,
                        timeout=int(param['TIMEOUT'])
                        )
        except Exception,e:
            if not DoesServiceExist(ssh,addr,22):
                raise MikrotikConnectException("SSH port is closed on %s"%addr)
            else:
                # If ssh port open, but we have another problem
                raise MikrotikConnectException(e)
        else:
	    sleep(0.5)
            return fn(self,ssh,custom)
        finally:
            ssh.close()
    return connect

def DoesServiceExist(self, host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((host, port))
        s.close()
    except:
        return False
    else:
        return True

class MikrotikException(Exception):pass
class MikrotikConnectException(MikrotikException):pass
class MikrotikSettingsException(MikrotikException):pass
