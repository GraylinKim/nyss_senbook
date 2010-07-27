from tornado.web import authenticated,RequestHandler
from settings import settings
from person import Person
import urllib

def normalizeName(user):
    return ''.join(re.match(r'(\w+)( |%20|\+)(\w+)',user).groups()[0:3:2]).lower()
    
class BaseHandler(RequestHandler):
    """A Base Handle for adding global functionality at a later point"""
    
    def get_current_user(self):
        """This is an internal override to work with authentication"""
        return self.get_secure_cookie("uname")
        
    def render(self,template_name, **kwargs):
            
        options = dict(dict(
            #Put default values for variables send to all classes here
            user=self.current_user,
            message=None,
            getname=lambda x: x.split(',')[0][3:],
            settings=settings,
            url=self.request.path,
        ).items() + kwargs.items())
        
        super(BaseHandler,self).render(template_name, **options)

class MainHandler(BaseHandler):
    def get(self):
        self.render(
            'templates/index.html',
            title='Search for your NY Senate Homies')

class PersonHandler(BaseHandler):
    def get(self,user):
        try:
            person = Person(urllib.unquote_plus(user))
        except StopIteration as e:
            self.render('templates/nomatch.html',title="No Such Person")
            return
        
        if self.current_user == person.name:
            self.render(
                'templates/edit_person.html',
                title="Editing %s - Profile" % person.name,
                person=person)
        else:
            self.render(
                'templates/person.html',
                title="%s - Profile" % person.name,
                person=person,)
    
    @authenticated
    def post(self,user):
        person = Person(urllib.unquote_plus(user))
        
        args = self.request.arguments
        files = self.request.files
        if 'avatar' in files:
            avatar = files['avatar'][0]
            filename = '%s.%s' % (''.join(person.name.split()),avatar['filename'].split('.')[-1])
            person.data['avatar'] = settings['avatars']+filename
            with open(settings['server_root']+'static/'+person.data['avatar'],'w') as outfile:
                outfile.write(avatar['body'])
        
        if 'aboutme' in args:
            person.data['aboutme'] = args.get('aboutme')
            
        person.save()
        self.redirect('')
        return
        
        
class GroupHandler(BaseHandler):
    def get(self,group):
        
        try:
            server = settings['ldap'].connect()
            group = urllib.unquote_plus(group)
            filterstr = '(&(cn=%s)(objectClass=dominoGroup))' % group
            name, data = server.search(filterstr).next()
            self.render(
                'templates/group.html',
                title="%s - Profile" % name,
                data=data,
                name=name,)
                
        except StopIteration as e:
            self.render('templates/no_match.html',title="No Such Group")

################################################################################
# Search Handlers

class SearchRouter(BaseHandler):
    def get(self):
        self.redirect("/")
        
    def post(self):
        if self.get_argument("group",None):
            oclass = "group"
        elif self.get_argument("person",None):
            oclass = "person"
        else:
            raise ValueError("Someone posted in a bad way")
        
        self.redirect('/search/%s/%s' % (oclass,self.get_argument("term","")))
        
class SearchHandler(BaseHandler):
    def get(self,otype,term):
        server = settings['ldap'].connect()  
        filterstr = '(&(cn=*%s*)(objectClass=domino%s))' % (term,otype)
        results = [result for result in server.search(filterstr)]
        self.render(
            'templates/search.html',
            title="%s Search Results (%s)" % (otype,len(results)),
            results = results,
            term = term,)

################################################################################
# Login Handlers

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
            self.redirect('/person/%s' % urllib.quote_plus(name))
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
        if 'ret' in self.request.arguments:
            self.redirect(self.request.arguments['ret'][0].replace(' ','+'))
        else:
            self.redirect("/")
