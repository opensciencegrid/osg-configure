#!/bin/sh

# First, install osg-configure
yum -y install python

python /osg-configure/setup.py install

# Next, run the tests
python /osg-configure/tests/run-osg-configure-tests 

