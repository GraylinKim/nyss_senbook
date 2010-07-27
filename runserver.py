#!/usr/bin/python

import tornado.web
import tornado.ioloop
import tornado.httpserver

from handlers import *
from settings import settings
from database import Couch,Ldap,Mysql


# Create, Configure, and Connect to couchdb, store connection in settings
if 'couch_settings' in settings:
    settings['couch'] = Couch(**settings['couch_settings'])

# Create, Configure, and Connect to couchdb, store connection in settings
if 'mysql_settings' in settings:
    settings['mysql'] = Mysql(**settings['mysql_settings'])

# Create, Configure, and Connect to ldap, store conncetion in settings
if 'ldap_settings' in settings:
    settings['ldap'] = Ldap(**settings['ldap_settings'])

#Configure the URL routing and create the application from settings
application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/person/([A-Z\+\%\*\._\-a-z0-9]+)/?', PersonHandler),
        (r'/group/([A-Z\+\%\*\._\-a-z0-9]+)/?', GroupHandler),
        (r'/search/?', SearchRouter ),
        (r'/search/(.+?)/(.+?)/?', SearchHandler ),
        (r'/login/?', LoginHandler ),
        (r'/logout/?', LogoutHandler ),
    ], **settings)


if __name__ == '__main__':

    #Create a server for our application
    http_server = tornado.httpserver.HTTPServer(application)

    #Give it a port to listen on, from settings
    http_server.listen(settings['port'])
    
    # start the tornado application
    tornado.ioloop.IOLoop.instance().start()
