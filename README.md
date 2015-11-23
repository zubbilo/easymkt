# EASYMKT tool

EasyMKT helps to sysadmins in automated backups, changing
users/passwords on lot of mikrotik devices from command line
or from some scheduler (crontab).

Tool can send Email Reports with full information about
backuped devices. Plus email reports supporting links to
storage with backups (by default links for elFinder 2.0).

NO need to run under ROOT!

# PREINSTALL

apt-get install python-setuptools python-jinja2 python-paramiko

## Check the Python version before using next command (python -V)
tar -xf scp.tar.gz -C /usr/local/lib/python2.X/dist-packages/

# INSTALL

python setup.py install

# UNINSTALL

apt-get install python-pip
pip uninstall easymkt

OR

just remove files:

/usr/local/lib/python2.7/dist-packages/easymkt

/usr/local/lib/python2.7/dist-packages/scp-0.7.1/

/usr/local/lib/python2.7/dist-packages/scp.py

/usr/local/lib/python2.7/dist-packages/scp.pyc

