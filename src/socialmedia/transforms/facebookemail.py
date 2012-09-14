#!/usr/bin/env python

from json import loads
import mechanize
import cookielib
from os import path
from urllib import urlencode
from sploitego.config import config
from sploitego.maltego.utils import debug
from sploitego.framework import configure
from sploitego.maltego.message import EmailAddress, AffiliationFacebook, Label
from easygui import multpasswordbox
import sploitego.hacks.gui
import time


__author__ = 'leres'
__copyright__ = 'Copyright 2012, Socialmedia Project'
__credits__ = []

__license__ = 'GPL'
__version__ = '0.1'
__maintainer__ = 'leres'
__email__ = 'twitleres@gmail.com'
__status__ = 'Development'

__all__ = [
    'dotransform'
]


def init_browser():

    cookies = cookielib.MozillaCookieJar(config['mechanize/cookie_jar'])

    browser = mechanize.Browser()

    browser.set_cookiejar(cookies)
    browser.set_handle_redirect(True)
    browser.set_handle_robots(False)
    browser.set_handle_equiv(True)
    browser.set_handle_gzip(False)
    browser.set_handle_referer(True)
    browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    browser.addheaders = [('User-Agent', 'Mozilla')]

    return browser, cookies

def login(browser, cookies):

    if not path.exists(config['mechanize/cookie_jar']):

        u, p = multpasswordbox("Enter your facebook credentials.","Facebook Login",["Email", "Password"]);

        credentials = {
            'email' : u,
            'pass' : p,
            'default_persistent' : 1,
            'lsd' : 'aaaaaaaa',
            'charset_test' : '%E2%82%AC%2C%C2%B4%2C%E2%82%AC%2C%C2%B4%2C%E6%B0%B4%2C%D0%94%2C%D0%84',
            'timezone' : '240',
            'lgnrnd' : '000000_0A0A',
            'lgnjs' : int(time.time()),
            'local' : 'en_US'
        }

        browser.open("https://www.facebook.com/")
        r = browser.open("https://www.facebook.com/login.php?login_attempt=1", urlencode(credentials))
        if r.code == 200:
            cookies.save(ignore_discard=True, ignore_expires=True)
    else:
        cookies.load(config['mechanize/cookie_jar'], ignore_discard=True, ignore_expires=True)

    fb_cookies = cookies._cookies['.facebook.com']['/']

    return fb_cookies['c_user'].value if 'c_user' in fb_cookies else 0


def getuser(browser, uid, email):

    if uid:

        data = {
            'viewer': uid,
            'value': email,
            '__a' : 1
        }

        r = browser.open("http://www.facebook.com/ajax/typeahead/search.php?%s" % urlencode(data))

        if r.code == 200:
            s = r.read()
            json = loads(s[s.find('{'):])

            if 'error' in json:
                raise Exception("%s: %s" % (json['errorSummary'], json['errorDescription']))
	    if json['payload']['entries']:
		debug(json['payload']['entries'][0])
            	return json['payload']['entries'][0]

    return None


@configure(
    label='Email lookup at facebook.com',
    description='Search if email has a facebook account',
    uuids=[ 'socialmedia.facebook.email' ],
    inputs=[ ( 'Socialmedia', EmailAddress ) ],
    debug=True
)
def dotransform(request, response):

    browser, cookies = init_browser()
    uid = login(browser, cookies)
    u = getuser(browser, uid, request.value)

    if u is None:
	return response
    else:
	    e = AffiliationFacebook(u['text'])
	    e.profileurl = 'http://www.facebook.com%s' % u['path']
	    e.name = u['text']
	    e.uid = u['uid']
	    e += Label('Facebook Link','<A href=http://www.facebook.com%s>Link</A>' % u['path'])
	    e += Label('Profile Picture', '<A href=%s>Link</A>' % u['photo'])
	    response += e
	    return response
    
