#!/usr/bin/python

import tornado.web
import tornado.ioloop
import tornado.httpserver

from database import Database
from settings import settings
from handlers import MainHandler

# Create, Configure, and Connect to couchdb, store connection in settings
settings['db'] = Database(**settings['db_settings']).configure().connect()

#Configure the URL routing and create the application from settings
application = tornado.web.Application([
        (r'/', MainHandler),
    ], **settings)

#Create a server for our application
http_server = tornado.httpserver.HTTPServer(application)

#Give it a port to listen on, from settings
http_server.listen(settings['port'])


if __name__ == '__main__':
    # start the tornado application
    tornado.ioloop.IOLoop.instance().start()
