from tornado.web import authenticated,RequestHandler
from settings import settings
from people import Person,fromName,fromId,authenticate,getNameFromUID
from project import Project
from group import Group
from urllib import quote_plus, unquote_plus

################################################################################

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
        
################################################################################

class MainHandler(BaseHandler):
    def get(self):
        self.render('templates/index.html',
            title='Search for your NY Senate Workers')

class PersonIdRouter(BaseHandler):
    def get(self,uid):
        people = fromId(uid)
        if len(people)==0:
            self.render('templates/noperson.html',title="No Such Person")
        elif len(people)!=1:
            self.render('templates/whichperson.html',title="Mutple Matches",people=people)
        else: #len(people)==1:
            person = people[0]
            args = (person.name,uid)
            self.redirect(quote_plus( '/person/%s (%s)' % args ,'+()/' ))
            
class PersonNameRouter(BaseHandler):
    def get(self,name):
        people = fromName(name)
        if len(people)==0:
            self.render('templates/noperson.html',title="No Such Person")
        elif len(people)!=1:
            self.render('templates/whichperson.html',title="Mutiple Matches",people=people)
        else: #len(people)==1:
            person = people[0]
            args = (unquote_plus(name),person.data['uid'])
            self.redirect(quote_plus( '/person/%s (%s)' % args ,'+()/' ))
        
class PersonHandler(BaseHandler):
    def get(self,name,uid):
        people = fromId(uid)
        if len(people)==0:
            self.render('templates/noperson.html',title="No Such Person")
            return
        if len(people)!=1:
            self.render('templates/whichperson.html',title="Mutple Matches",people=people)
            return
        
        person = people[0]
        if self.current_user == person.name:
            self.render('templates/edit_person.html',
                title="Editing %s - Profile" % person.name,
                person=person)
        else:
            self.render('templates/person.html',
                title="%s - Profile" % person.name,
                person=person)
    
    @authenticated
    def post(self,name,uid):
        people = fromId(uid)
        
        if len(people)==1:
            person = people[0]
            
            args = self.request.arguments
            files = self.request.files
            if 'avatar' in files:
                person.set_avatar(files['avatar'][0])
            if 'aboutme' in args:
                person.data['aboutme'] = args.get('aboutme')
                
            person.save()
            
        self.redirect('')
        
class GroupHandler(BaseHandler):
    def get(self,name):
        
        try:
            group = Group(unquote_plus(name))
            self.render('templates/group.html',
                title="%s - Profile" % group.data['displayname'],
                data=group.data,
                name=group.id)
                
        except StopIteration as e:
            self.render('templates/no_match.html',title="No Such Group")

class ProjectHandler(BaseHandler):
    def get(self,project):
        project = Project(unquote_plus(project))
        self.render('templates/project.html',
            title="Project %s" % project,
            project = project)
            
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
        results = server.search(filterstr)
        self.render('templates/search.html',
            title="%s Search Results (%s)" % (otype,len(results)),
            results = results,
            term = term)

################################################################################
# Login Handlers

class LoginHandler(BaseHandler):
        
    def get(self):
        if self.current_user:
            self.redirect('/person/%s' % quote_plus(self.current_user))
        else:
            self.render('templates/login.html',title="Login")
        
    def post(self):
        who = self.get_argument("who")
        cred = self.get_argument("cred")
        
        if authenticate(who,cred):
            name = getNameFromUID(who)
            self.set_secure_cookie("uid",who)
            self.set_secure_cookie("uname",name)
            self.redirect('/person/%s' % quote_plus(name))
        else:
            self.render('templates/login.html',
                title="Login",
                message="Authentication Failed")
        
class LogoutHandler(BaseHandler):
    def get(self):
        if self.current_user:
            self.clear_cookie("uid")
            self.clear_cookie("uname")
        if 'ret' in self.request.arguments:
            self.redirect(self.request.arguments['ret'][0].replace(' ','+'))
        else:
            self.redirect("/")
