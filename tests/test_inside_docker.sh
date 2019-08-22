#!/bin/bash

set -exu

OS_VERSION=$1
OSG_VERSION=$2

# Clean the yum cache
yum -y clean all

ls -l /home

# First, install all the needed packages.
rpm -U https://dl.fedoraproject.org/pub/epel/epel-release-latest-${OS_VERSION}.noarch.rpm
yum -y install yum-plugin-priorities
rpm -U https://repo.opensciencegrid.org/osg/${OSG_VERSION}/osg-${OSG_VERSION}-el${OS_VERSION}-release-latest.rpm

yum -y install condor-python make

# First, install osg-configure
cd /osg-configure
make install

# Next, run the tests
python tests/run-osg-configure-tests

