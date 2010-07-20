import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    """A Base Handle for adding global functionality at a later point"""

class MainHandler(BaseHandler):
    def get(self):
        self.render('templates/index.html', title='Search for your NASA Homies')
