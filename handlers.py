import tornado.web
from settings import settings
import urllib

class BaseHandler(tornado.web.RequestHandler):
    """A Base Handle for adding global functionality at a later point"""

class MainHandler(BaseHandler):
    def get(self):
        self.render('templates/index.html', title='Search for your NY Senate Homies')
        
class PersonHandler(BaseHandler):
    def get(self,user):
        user = urllib.unquote_plus(user)
        results = settings['ldap'].search('cn=%s' % user)
        name, data = results.next()
        self.render('templates/person.html',title="%s - Profile" % name,data=data, name=name )
        return
