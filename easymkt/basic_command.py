from base import MikrotikConnectException, MikrotikException, connect_to_mikrotik
import re
from scp import SCPClient
from time import sleep

class BasicCommand(object):


    @connect_to_mikrotik
    def MikrotikIdentity(self,ssh,custom=None):
        try:
            command = 'system identity print'
	    stdin, stdout, sterr = ssh.exec_command(command)
	    exit_status = stdout.channel.recv_exit_status()
	    sleep(1)
        except Exception,e:
	    raise MikrotikException('Error while geting identity: %s'%e)
        else:
    	    out = stdout.read()
            matchObj = re.match(r"name: (.*)",out.strip(), re.M|re.I)
	    identity = matchObj.group(1) if matchObj else None
            return identity

    @connect_to_mikrotik
    def MikrotikExport(self,ssh,filename):
        try:
            command = 'export file=%s; system identity print'%(filename)
            stdin, stdout, stderr = ssh.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            sleep(5)
        except Exception,e:
            raise MikrotikException(e)
        else:
    	    out = stdout.read()
    	    match = re.search(r"name: ",out.strip(), re.M|re.I)
    	    if match:
        	return True
    	    else:
    		raise MikrotikException("BUG detected: Export not finished! Do it manually.")
    
    @connect_to_mikrotik
    def MikrotikTextExport(self,ssh,custom=None):
        try:
            command = 'export'
            stdin, stdout, stderr = ssh.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            sleep(5)
        except Exception,e:
            raise MikrotikException(e)
        else:
            out = stdout.read().strip()
            if out.startswith('excepted') or out.startswith('failure'):
                raise MikrotikException(out)
            return out
            
    @connect_to_mikrotik
    def MikrotikBackup(self,ssh,filename):
        try:
            command = 'system backup save name=%s'%(filename)
            stdin, stdout, stderr = ssh.exec_command(command)
        except Exception,e:
            raise MikrotikException(e)
        else:
            out = stdout.read().strip()
            if out == "Configuration backup saved" or out == None:
                return True
            elif out.startswith('excepted') or out.startswith('failure'):
                raise MikrotikException(out)      
            else:
                return True

    @connect_to_mikrotik
    def MikrotikNewUser(self,ssh,userparam):
        try:
            command = 'user add name=%(user)s group=%(group)s password=%(pass)s'%userparam
            stdin, stdout, stderr = ssh.exec_command(command)
        except Exception,e:
            raise MikrotikException(e)
        else:
            out = stdout.read().strip()
            if out.startswith('excepted') or out.startswith('failure'):
                raise MikrotikException(out)
            return out

    @connect_to_mikrotik
    def MikrotikModUser(self,ssh,userparam):
        try:
            command = 'user set %(user)s group=%(group)s password=%(pass)s'%userparam
            stdin, stdout, stderr = ssh.exec_command(command)
        except Exception,e:
            raise MikrotikException(e)
        else:
            out = stdout.read().strip()
            if out.startswith('excepted') or out.startswith('failure'):
                raise MikrotikException(out)
            return out

    @connect_to_mikrotik
    def MikrotikDelUser(self,ssh,userparam):
        try:
            command = 'user remove %(user)s'%userparam
            stdin, stdout, stderr = ssh.exec_command(command)
        except Exception,e:
            raise MikrotikException(e)
        else:
            out = stdout.read().strip()
            if out.startswith('excepted') or out.startswith('failure'):
                raise MikrotikException(out)
            return out

    @connect_to_mikrotik
    def MikrotikSFTP(self,ssh,getfile):
        try:
	    scp = SCPClient(ssh.get_transport())
	    scp.get(getfile['file'],getfile['saveto'])
        except Exception,e:
            raise MikrotikException("SCPClient download error %s"%e)
        else:
            return True
        finally:
            pass

    @connect_to_mikrotik
    def MikrotikClean(self,ssh,filename):
        try:
            command = 'file remove "%s"'%(filename)
            stdin, stdout, stderr = ssh.exec_command(command)
        except Exception,e:
            raise MikrotikException('Clean cancel with error: %s, stdout: %s'%(e,stdout.read()))
        else:
            return True
