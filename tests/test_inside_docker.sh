#!/bin/sh

OS_VERSION=$1

# Clean the yum cache
yum -y clean all

ls -l /home

# First, install all the needed packages.
rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-${OS_VERSION}.noarch.rpm
yum -y install yum-plugin-priorities
rpm -Uvh https://repo.opensciencegrid.org/osg/3.4/osg-3.4-el${OS_VERSION}-release-latest.rpm

yum -y install python condor-python make --enablerepo=osg-minefield

# First, install osg-configure
cd /osg-configure
make install

# Next, run the tests
python tests/run-osg-configure-tests

