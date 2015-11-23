#!/usr/bin/env python

from setuptools import setup
import os

setup(name="easymkt",
      version="0.4.1",
      description="Mikrotik Library for automatization work with network infrastructure.",
      classifiers=[],
      keywords="mikrotik easybox",
      author="Sergey Suglobov / Egor Minko",
      author_email="scarchik@gmail.com,egor.minko@gmail.com",
      url="https://github.com/zubbilo",
      license="MIT",
      packages=["easymkt"],
      include_package_data = True,
      data_files=[('easymkt',['easymkt/settings.cfg','easymkt/mail_template.html'])],
      )

try:
    os.system('cp easymkt.py /usr/local/bin/easymkt')
except Exception,e:
    print e
