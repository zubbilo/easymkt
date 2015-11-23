# -*- coding: utf-8 -*-
from base import MikrotikBase, MikrotikException, MikrotikConnectException
from basic_command import BasicCommand
from paramiko import SFTPClient
from defines import *
import os, logging
import scp

class ExportDevices(MikrotikBase, BasicCommand):
        
    def __init__(self):
        MikrotikBase.__init__(self)
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',datefmt='%m/%d/%Y %H:%M', filename=self.parameters['LOG_FILE'], level=eval(self.parameters['LOG_LEVEL']))
     
    def main(self,action,devices,details):
        ssh = self.prepaire_connect()
        if action == 'one' or action == 'all':
            mikrotiks = [['%s'%devices]] if devices else self.mikrotiks
        elif action == 'list':
            mikrotiks = self.parse_devices(devices)

        # Calc total mikrotik for summary report
        total = len(mikrotiks)
        
        for mikrotik in mikrotiks:
            try:
                addr = mikrotik[0]
                name = mikrotik[1] if len(mikrotik) >= 2 else None
                place = mikrotik[2] if len(mikrotik) >= 3 else None
            except KeyError,e:
                raise MikrotikException, "Device list error. Check device list format. Message: %s"%e
            else:
                logging.info(" ===> Starting Export for %s (%s)"%(name,addr))
            
            identity, sftp = None, None
            
            """Default report parameters"""
            report = {
                      'addr':addr, 'name':name, 'location':place,
                      'file':None, 'status':None, 'error':None, 'clean':None,
                      'finally':None, 'class':None, 'dir':None
                      }
            
            """Get Mikrotik Identity"""
            try:
                identity = self.MikrotikIdentity(ssh,addr,self.parameters)
            except MikrotikConnectException as msg:
                report['error'] = "Connect %s"%msg
                logging.warning('Not connected to mikrotik %s, because of %s'%(addr,msg))
            except MikrotikException as msg:
                report['error'] = "Error %s"%msg
                logging.error('Error getting identity %s'%msg)
            else:
                logging.info("Get identity success for %s (%s)"%(name,addr))
                name = identity
                report['name'] = name

            """Choose filename and dirname"""
            filename = "%s_%s"%(self.version, identity.replace(' ', '_').replace('"','')) if identity else "%s_%s"%(self.version, name)
            dirname = "%s"%(identity.replace(' ', '_').replace('"','')) if identity else "UNKNOWN"
            report['file'], report['dir'] = filename, dirname

            """Check exist Export before start create new"""
            if self.check_file_exist(filename,dirname,type='.rsc'):
                logging.info("File(%s) with export alredy exist."%(filename))
                report['status'] = STATUS_EXIST
            elif not report['error']:
                logging.info("Init Export for %s (%s)"%(name,addr))
                """Create Export file on mikrotik"""
                try:
                	bkp = self.MikrotikExport(ssh,addr,self.parameters,filename)
                except MikrotikConnectException as msg:
                	report['error'] = msg
                	logging.warning(msg)
                except MikrotikException as msg:
                	report['error'] = msg
                	logging.error(msg)
                else:
                    logging.info("Create Export success for %s (%s)"%(name,addr))
                finally:
                	report['status'] = STATUS_FAIL if report['error'] else STATUS_OK
            else:
                report['status'] = STATUS_FAIL

            """Get Export file from mikrotik"""
            # Check errors. If we have error on previous step - break sftp backup download.
            if report['status'] == STATUS_FAIL: 
                report['finally'] = FINALLY_FAIL
            elif report['status'] == STATUS_EXIST:
                report['finally'] = FINALLY_EXIST
            else:
                # Prepaire filename and directory for backup
                filename = report['file'] + ".rsc"
                pwdsave = self.parameters['BKP_DIR'] + report['dir'] + "/" + filename
                getfile = {'file':filename,'saveto':pwdsave}
                # Go for backup file
                try:
                    logging.info("Init SCP fetch Export from %s (%s)"%(name,addr))
                    self.MikrotikSFTP(ssh,addr,self.parameters,getfile)
                except MikrotikConnectException as msg:
                    report['error'] = msg
                    logging.warning(msg)
                    report['finally'] = FINALLY_FAIL
                except MikrotikException as msg:
                    report['error'] = msg
                    logging.error(msg)
                    report['finally'] = FINALLY_FAIL
                else:
                    report['finally'] = FINALLY_OK
                    logging.info("Fetch success %s (%s)"%(name,addr))

                if report['status'] == STATUS_OK:
                    """Clean Export file on mikrotik"""
                    try:
                        filename = report['file'] + '.rsc'
                        logging.info("Removing Export file %s from %s (%s)"%(filename,name,addr))
                        clean = self.MikrotikClean(ssh,addr,self.parameters,filename)
                    except MikrotikConnectException as msg:
                        logging.warning('Removing file %s failed on %s, because of: %s'%(filename,addr,msg))
                    except MikrotikException as msg:
                        logging.error('Removing file %s failed on %s, because of: %s'%(filename,addr,msg))
                    else:
                        if clean:
                            report['clean'] = 'Success'
                        logging.info("Clean success for %s (%s)"%(name,addr))

            self.reports.append(report)
            
            # Output report to console
            self.view_report(details,report)
            
        """Send Report"""
        if details['mailreport']:
            self.send_report('export',total)
