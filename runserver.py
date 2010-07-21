#!/usr/bin/python

import tornado.web
import tornado.ioloop
import tornado.httpserver

from database import Database
from settings import settings
from ldapter import ldapter
from handlers import MainHandler,PersonHandler


# Create, Configure, and Connect to couchdb, store connection in settings
settings['db'] = Database(**settings['db_settings']).configure().connect()

# Create, Configure, and Connect to ldap, store conncetion in settings
settings['ldap'] = ldapter(**settings['ldap_settings']).connect()

#Configure the URL routing and create the application from settings
application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/person/([A-Z\+\%\._\-a-z0-9]+)/?', PersonHandler),
    ], **settings)

#Create a server for our application
http_server = tornado.httpserver.HTTPServer(application)

#Give it a port to listen on, from settings
http_server.listen(settings['port'])


if __name__ == '__main__':
    # start the tornado application
    tornado.ioloop.IOLoop.instance().start()
