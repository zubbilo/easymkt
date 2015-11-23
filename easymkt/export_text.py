# -*- coding: utf-8 -*-
from base import MikrotikBase, MikrotikException, MikrotikConnectException
from basic_command import BasicCommand
from defines import *
from time import sleep
import logging

class ExportTextDevices(MikrotikBase, BasicCommand):
    
    def __init__(self):
        MikrotikBase.__init__(self)
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',datefmt='%m/%d/%Y %H:%M', filename=self.parameters['LOG_FILE'], level=eval(self.parameters['LOG_LEVEL']))

    def main(self,action,devices,details):
        # Prepaire ssh connection
        ssh = self.prepaire_connect()
        
        # Read action and prepaire list
        if action == 'one' or action == 'all':
            mikrotiks = [['%s'%devices]] if devices else self.mikrotiks
        elif action == 'list':
            mikrotiks = self.parse_devices(devices)
        
        # Calc total mikrotik for summary report
        total = len(mikrotiks)
        
        # Start do export for mikrotiks
        for mikrotik in mikrotiks:
            try:
                addr = mikrotik[0]
                name = mikrotik[1] if len(mikrotik) >= 2 else None
                place = mikrotik[2] if len(mikrotik) >= 3 else None
                identity = None
            except KeyError,e:
                raise MikrotikException, "Device list error. Check device list format. Message: %s"%e
            else:
                logging.info(" ===> Starting TEXT export for %s (%s)"%(name,addr))
            
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
                report['error'] = msg
                logging.warning(msg)
            except MikrotikException as msg:
                report['error'] = msg
                logging.error(msg)
            else:
                logging.info("Get identity success for %s (%s)"%(name,addr))
                name = identity
                report['name'] = name
                
            """Choose filename and dirname"""
            filename = "%s_%s"%(self.version, identity.replace(' ', '_').replace('"','')) if identity else "%s_%s"%(self.version, name)
            dirname = "%s"%(identity.replace(' ', '_').replace('"','')) if identity else "UNKNOWN"
            report['file'], report['dir'] = filename, dirname

            """Check exist export before start create new"""
            if self.check_file_exist(filename,dirname,type='.rsc'):
                logging.info("File(%s) with export alredy exist."%(filename))
                report['status'] = STATUS_EXIST
            elif not report['error']:
                """Create export and save it in file on server"""
                try:
                    logging.info("Init Text Export on %s (%s)"%(name,addr))
                    config = self.MikrotikTextExport(ssh,addr,self.parameters)
                except MikrotikConnectException as msg:
                    report['error'] = msg
                    logging.warning(msg)
                except MikrotikException as msg:
                    report['error'] = msg
                    logging.error(msg)
                else:
                    filename = report['file'] + ".rsc"
                    pwdsave = self.parameters['BKP_DIR'] + report['dir'] + "/" + filename
                    with open(pwdsave,'w+') as f:
                        f.write(config)
                    logging.info("Export collected and saved to LOCAL file %s for %s (%s)"%(filename,name,addr))
                finally:
                    report['status'] = STATUS_FAIL if report['error'] else STATUS_OK
            else:
                report['status'] = STATUS_FAIL
            
            self.reports.append(report)
            
            # Output report to console
            self.view_report(details,report)
            
        """Send Report"""
        if details['mailreport']:
            self.send_report('export', total)
