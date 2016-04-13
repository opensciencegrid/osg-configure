#!/bin/sh

OS_VERSION=$1

ls -l /home

# First, install all the needed packages.
rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-${OS_VERSION}.noarch.rpm
yum -y install yum-plugin-priorities
rpm -Uvh https://repo.grid.iu.edu/osg/3.3/osg-3.3-el${OS_VERSION}-release-latest.rpm

yum -y install python condor-python

# First, install osg-configure
cd /osg-configure
python setup.py install

# Next, run the tests
python tests/run-osg-configure-tests 

