import tornado.web
from settings import settings
from ldapter import ldapter
import urllib

class BaseHandler(tornado.web.RequestHandler):
    """A Base Handle for adding global functionality at a later point"""
    
    def get_current_user(self):
        """This is an internal override to work with authentication"""
        return self.get_secure_cookie("uname")
        
    def render(self,template_name, **kwargs):
            
        options = dict(dict(
            #Put default values for variables send to all classes here
            user=self.current_user,
            message=None,
        ).items() + kwargs.items())
        
        super(BaseHandler,self).render(template_name, **options)

class MainHandler(BaseHandler):
    def get(self):
        self.render('templates/index.html', title='Search for your NY Senate Homies')

class PersonHandler(BaseHandler):
    def get(self,user):
        try:
            user = urllib.unquote_plus(user)
            server = settings['ldap'].connect()
            
            query = server.search('(&(cn=%s)(objectClass=dominoPerson))' % user)
            ident, data = query.next()
            name = data.pop('cn',[ident,])[0]
            
            query = server.search('(&(member=%s)(objectClass=dominoGroup))' % ident)
            groups = [result for result in query]
            
            self.render(
                'templates/person.html',
                title="%s - Profile" % name,
                data=data,
                name=name,
                groups=groups
            )
        except StopIteration as e:
            self.render('templates/nomatch.html',title="No Such Person")
        return
        
class GroupHandler(BaseHandler):
    def get(self,group):
        
        try:
            group = urllib.unquote_plus(group)
            query = settings['ldap'].connect().search('(&(cn=%s)(objectClass=dominoGroup))' % group)
            name, data = query.next()
            self.render(
                'templates/group.html',
                title="%s - Profile" % name,
                data=data,
                name=name,
                getname=lambda x: x.split(',')[0][3:],)
                
        except StopIteration as e:
            self.render('templates/nomatch.html',title="No Such Group")
        return
        
class SearchHandler(BaseHandler):
    def get(self,otype,term):
        term = "*"+term+"*" #Make it fuzzy
        objectClass = "domino"+otype[0].upper()+otype[1:] #create the objectClass
        query = settings['ldap'].connect().search('(&(cn=%s)(objectClass=%s))' % (term,objectClass))
        results = [result for result in query]
        self.render(
            'templates/search.html',
            title="%s Search Results (%s)" % (objectClass[6:],len(results)),
            results = results,
            term = term,)
        
class LoginHandler(BaseHandler):
    
    def getUserName(self, who):
        record = settings['ldap'].search("(uid=%s)" % who).next()
        return record[1]['cn'][0]
        
    def get(self):
        if self.current_user:
            name = self.current_user
            self.redirect('/person/%s' % urllib.quote_plus(name))
        else:
            self.render(
                'templates/login.html',
                title="Login",)
        
    def post(self):
        who = self.get_argument("who")
        cred = self.get_argument("cred")
        
        if settings['ldap'].simple_auth(who,cred):
            name = self.getUserName(who)
            self.set_secure_cookie("uid",who)
            self.set_secure_cookie("uname",name)
            self.redirect('/person/%s',urllib.quote_plus(name))
        else:
            self.render(
                'templates/login.html',
                title="Login",
                message="Authentication Failed",)
        
class LogoutHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.clear_cookie("uid")
            self.clear_cookie("uname")
            
        self.redirect("/")
