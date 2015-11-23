#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Configure this script in settings.py file.
# It must be in directory with script.

import sys
import easymkt

if __name__ == "__main__":
    try:
        action = sys.argv[1]
    except:
        print easymkt.usage()
    else:
        easymkt.main(action, sys.argv[2:])
