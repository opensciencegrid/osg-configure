#!/bin/sh

# First, install osg-configure
yum -y install python

cd /osg-configure

python setup.py install

# Next, run the tests
python tests/run-osg-configure-tests 

