#!/usr/bin/python

import os
import re
import pwd
import json
import pipes
import urllib
import httplib
import urllib2

from osg_configure.modules import exceptions

_debug = False

# defaults
#default_capath  = "/etc/grid-security/certificates/"
default_certpath = "/etc/grid-security/hostcert.pem"
default_keypath  = "/etc/grid-security/hostkey.pem"

# curl example:
# curl --capath /etc/grid-security/certificates/ --cert /etc/grid-security/hostcert.pem --key /etc/grid-security/hostkey.pem 'https://fermicloud331.fnal.gov:8443/gums/json/getOsgVoUserMap?hostname=test.cs.wisc.edu'

# see: http://stackoverflow.com/questions/1875052/using-paired-certificates-with-urllib2
class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
    def __init__(self, certpath, keypath):
        urllib2.HTTPSHandler.__init__(self)
        self.certpath = certpath
        self.keypath = keypath

    def https_open(self, req):
        return self.do_open(self.get_connection, req)

    # wrapper for HTTPSConnection constructor with cert files
    def get_connection(self, host, timeout=60):
        return httplib.HTTPSConnection(host, key_file=self.keypath,
                                             cert_file=self.certpath,
                                             timeout=timeout)

def certurlopen(url, certpath, keypath):
    handler = HTTPSClientAuthHandler(certpath, keypath)
    opener  = urllib2.build_opener(handler)
    return opener.open(url)

def get_subject(certpath):
    # TODO: use some SSL/X509 python module to extract DN
    subject = os.popen("openssl x509 -in %s -noout -subject" %
                       pipes.quote(certpath)).read()
    pfx = "subject="
    if subject.startswith(pfx):
        subject = subject[len(pfx):]
    return subject.strip()

def gums_json_map(gums_host, command, params, certpath, keypath):
    params = urllib.urlencode(params)
    if not re.search(r':\d+$', gums_host):
        gums_host = gums_host + ":8443"
    url = 'https://%s/gums/json/%s?%s' % (gums_host, command, params)
    handle = certurlopen(url, certpath, keypath)
    return json.load(handle)

def user_exists(user):
    try:
        pwd.getpwnam(user)
        return True
    except KeyError:
        return False

def supported_vos_for_vo_users(vo_users):
    def any_vo_user_exists(vo):
        return any( user_exists(user) for user in vo_users[vo] )

    return sorted(filter(any_vo_user_exists, vo_users))

def gums_json_vo_user_map(gums_host, target_host=None,
                          certpath=default_certpath, keypath=default_keypath):
    json_cmd = "getOsgVoUserMap"
    if target_host is None:
        target_host = get_subject(certpath)
    params   = {'hostname': target_host}
    try:
        json_map = gums_json_map(gums_host, json_cmd, params, certpath, keypath)
    except EnvironmentError, e:
        raise exceptions.ApplicationError(
            "Error contacting gums host via json interface: %s" % e)

    if _debug:
        print json_map

    if 'result' not in json_map:
        raise exceptions.ApplicationError("'result' not in returned json")
    if json_map['result'] != 'OK':
        raise exceptions.ApplicationError("%s: %s" % (
                    json_map.get('result', "Fail"),
                    json_map.get('message', "(no message)")))
    if 'map' not in json_map:
        raise exceptions.ApplicationError("Missing 'map' object")

    vo_users = json_map['map']

    if type(vo_users) is not dict:
        raise exceptions.ApplicationError("'map' object not of type dict")

    return vo_users

def gums_json_user_vo_map_file(gums_host, target_host=None,
                          certpath=default_certpath, keypath=default_keypath):
    json_cmd = "generateOsgUserVoMap"
    if target_host is None:
        target_host = get_subject(certpath)
    params   = {'hostname': target_host}
    try:
        json_map = gums_json_map(gums_host, json_cmd, params, certpath, keypath)
    except EnvironmentError, e:
        raise exceptions.ApplicationError(
            "Error contacting gums host via json interface: %s" % e)

    if _debug:
        print json_map

    if 'result' not in json_map:
        raise exceptions.ApplicationError("'result' not in returned json")
    if json_map['result'] != 'OK':
        raise exceptions.ApplicationError("%s: %s" % (
                    json_map.get('result', "Fail"),
                    json_map.get('message', "(no message)")))
    if 'map' not in json_map:
        raise exceptions.ApplicationError("Missing 'map' object")

    mapfile = json_map['map']

    return mapfile

def gums_supported_vos(gums_host, target_host=None,
                       certpath=default_certpath, keypath=default_keypath):
    vo_users = gums_json_vo_user_map(gums_host, target_host, certpath, keypath)
    return supported_vos_for_vo_users(vo_users)

