from backup import BackupDevices
from export import ExportDevices
from export_text import ExportTextDevices
from users import ModifyUser
from sys import exit
import os
import getopt

def usage():

    return  """
            Mikrotik version 0.3.0
            --------------------
            Usage: ./mkt {Function} {KEYS}
            
            Supported Functions:
            ---------
                help - Print this help page
            	    Supported keys: -none-
                
                config - Configure default script parameters.
                    Supported keys: -e
        
                newuser | usermod - Create new user | Modify exist user.
                    Supported keys: -u,-p,-g,[-a|-i|-l],-q,-v,-m
                    
                deluser - Delete user.
                    Supported keys: -u,[-a|-i|-l],-q,-v,-m 
                    
                backup - Create Backup of configuration.
                    Supported keys: [-a|-i|-l],-q,-v,-m 
                    
                export - Create Export of configuration from Mikrotik. Note: Internal Users not exporting!
                    Supported keys: [-a|-i|-l],-q,-v,-m 
                
                textexport - Create Export of configuration from Mikrotik with account with read-only rights.
        	    Supported keys: [-a,-i,-l],-q,-v,-m 
                        
            Supported KEYS:
            ---------
                -e {editor}, --editor {editor}    - choose editor which you like. For example: vim, nano, gedit.
                
                -u {string}, --username {string}
                
                -p {string}, --password {string}
                
                -g {perm}, --group {perm}         - set permissions for user. Available: read, write, full.
                
                -a, --all                         - choose all mikrotik from default list (device_list)
                
                -i {IP}, --address {IP}           - set mikrotik router IP address
                
                -l {filename}, --list {filename}  - set list of devices. Path to file.
                
                -q, --quite                       - execute without outputing report to console.
                
                -v, --verbose                     - output debug report to console.
                
                -m, --mailreport                  - send email report. Check for [mail] chapter in settings.cfg
            """ 

class Mikrotik(object):
    
    def main(self, action, keys):
        """Parse arguments and execute action"""
        
        COMMAND_NAME = 'mkt.py %s [-h] [-q,-v,-m] [-a,-i <address>, -l <list>] [-e <editor>] [-u <username>, -p <password>, -g <group>]'%action
        
        # Read arguments
        try:
            opts, args = getopt.getopt(keys,"i:l:e:u:p:g:ahqvm", ['address=',
                                                               'list=',
                                                               'editor=',
                                                               'username=',
                                                               'password=',
                                                               'group=',
                                                               'all',
                                                               'help',
                                                               'quite',
                                                               'verbose',
                                                               'mailreport'
                                                               ])
        except getopt.GetoptError:
            print COMMAND_NAME
        else:
            # Default arguments value
            all, address, dlist, username, password, group, editor = None, None, None, None, None, None, None
            quite, verbose, emailreport = False, False, False
            
            # Parse and check arguments
            for opt, arg in opts:
                if opt == '-h':
                    print usage()
                    exit()
                elif opt in ("-i", "--address"):
                    if self.validIP(arg):
                        address = arg
                    else:
                        print "Incorrect IP address."
                        exit()
                elif opt in ("-l", "--list"):
                    dlist = arg                
                elif opt in ("-a", "--all"):
                    all = True
                elif opt in ("-u", "--username"):
                    username = arg
                elif opt in ("-p", "--password"):
                    password = arg
                elif opt in ("-g", "--group"):
                    if arg not in ('read','write','full'):
                        print "Group access must be one of read|write|full"
                        exit()
                    else:
                        group = arg
                elif opt in ("-e", "--editor"):
                    editor = arg
                elif opt in ("-q", "--quite"):
                    quite = True
                elif opt in ("-v", "--verbose"):
                    verbose = True
                elif opt in ("-m", "--mailreport"):
                    emailreport = True

            # EconomPack 
            self.details = {'quite':quite,'verbose':verbose,'mailreport':emailreport}

        # DO ACTION
        if action == 'backup' or action == 'export' or action == 'textexport':
            if all and address:
                # Can't using 2 arguments
                print "Don't use -i,-a,-l keys together. Only one of them."
                exit()
            elif all and dlist:
                # Can't using 2 arguments
                print "Don't use -i,-a,-l keys together. Only one of them."
                exit()
            elif not all and not address and not dlist:
                # Nothink to do
                print usage()
                exit()
            elif all and action == 'backup':
                self.make_backup('all',None)
            elif address and action == 'backup':
                self.make_backup('one',address)
            elif dlist and action == 'backup':
                self.make_backup('list',dlist)
            elif all and action == 'export':
                self.make_export('all',None)
            elif address and action == 'export':
                self.make_export('one',address)
            elif dlist and action == 'export':
                self.make_export('list',dlist)
            elif all and action == 'textexport':
                self.make_textexport('all',None)
            elif address and action == 'textexport':
                self.make_textexport('one',address)
            elif dlist and action == 'textexport':
                self.make_textexport('list',dlist)
                
        elif action == 'newuser' or action == 'usermod': 
            if not username or not password or not group:
                # Not all parameters input
                print usage()
                exit()

            if all:
                self.users(action,'all',None,username,password,group)
            elif address:
                self.users(action,'one',address,username,password,group)
            elif dlist:
                self.users(action,'list',dlist,username,password,group)
                                 
        elif action == 'deluser':
            if not username:
                # Nothink to do
                print usage
                exit()

            if all:
                self.users(action,'all',None,username)
            elif address:
                self.users(action,'one',address,username)
            elif dlist:
                self.users(action,'list',dlist,username)

        elif action == 'config':
            if not editor:
                # Nothink to do
                print usage
                exit()
            else:
                self.set_config(action,editor)

        elif action == 'help':
            print usage()
            exit()
    
    def set_config(self, action, editor):
        """Set configuration"""
        file = os.path.join(os.path.dirname(__file__), 'settings.cfg')
        os.system('%s %s'%(editor, file))
    
    def make_backup(self, action, devices):
        """Execute Backup action"""
        BackupDevices().main(action, devices, self.details)
        
    def make_export(self, action, devices):
        """Execute Export action"""
        ExportDevices().main(action, devices, self.details)
        
    def make_textexport(self, action, devices):
        """Execute TextExport action"""
        ExportTextDevices().main(action, devices, self.details)
        
    def users(self, action, act, devices, user, password=None, group=None):
        """Execute user actions"""
        ModifyUser(action, act, devices, user, self.details, password, group).main()

    @staticmethod
    def validIP(address):
        """Return True if IP address is valid"""
        parts = address.split(".")
        if len(parts) != 4:
            return False
        for item in parts:
            if not 0 <= int(item) <= 255:
                return False
        return True
    
def main(action, keys=None):
    """Link to class Mikrotik"""
    Mikrotik().main(action, keys)
