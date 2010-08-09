#!/usr/bin/python

import tornado.web
import tornado.ioloop
import tornado.httpserver

from handlers import *
from settings import settings

#Configure the URL routing and create the application from settings

word = r'[A-Za-z\-\.]+'
space = r'[\+\%0-9 ]+'
sep = r'[\+\%0-9 ]*'
uid = r'[a-z\.]+'
lparen = r'(?:\(|%28)'
rparen = r'(?:\)|%29)'
application = tornado.web.Application([
        (r'/', MainHandler),
        (r'/person/(%s)' % uid, PersonIdRouter),
        (r'/person/(%s%s%s)' % (word,space,word), PersonNameRouter),
        (r'/person/(%s%s%s)%s%s(%s)%s/?' % (word,space,word,sep,lparen,uid,rparen), PersonHandler),
        (r'/group/([A-Z\+\%\*\._ \-a-z0-9]+)/?', GroupHandler),
        (r'/project/([A-Z\+\%\*\._\-a-z0-9\(\)]+)/?', ProjectHandler),
        (r'/search/?', SearchHandler ),
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
