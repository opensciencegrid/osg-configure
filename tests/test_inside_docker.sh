#!/bin/bash

set -exu

OS_VERSION=$1
OSG_VERSION=$2

# Clean the yum cache
yum -y clean all

ls -l /home

# First, install all the needed packages.
rpm -U https://dl.fedoraproject.org/pub/epel/epel-release-latest-${OS_VERSION}.noarch.rpm
[[ $OS_VERSION -gt 7 ]] || yum -y install yum-plugin-priorities
rpm -U https://repo.opensciencegrid.org/osg/${OSG_VERSION}/osg-${OSG_VERSION}-el${OS_VERSION}-release-latest.rpm

if [[ $OS_VERSION -gt 7 ]]; then
    yum -y install --enablerepo=osg-testing --enablerepo=PowerTools python3-condor python3 make
    PYTHON=python3
else
    yum -y install python2-condor make
    PYTHON=python2
fi

# First, install osg-configure
cd /osg-configure
make install PYTHON=$PYTHON

# Next, run the tests
$PYTHON tests/run-osg-configure-tests

