import urllib
from settings import settings


class RecordLoadError(Exception):
    pass

class LdapPerson(object):
    
    def __init__(self,result=None):
        if not result:
            self.data = dict()
        else:
            cn, self.data = result
            ldap = settings['ldap'].connect()
            filterstr = '(&(member=%s)(objectClass=dominoGroup))' % cn
            self.data['groups'] = [r for r in ldap.search(filterstr)]
            self.data['uid'] = self.data['uid'][0]
            self.data['name'] = self.data.get('givenname',[''])[0]+' '+self.data.get('sn',[''])[0]
        
    @classmethod
    def getRecords(self,key,value):
        try:
            ldap = settings['ldap'].connect()
            filterstr = '(&(%s=%s)(objectClass=dominoPerson))'        
            ldap_results = ldap.search( filterstr % (key,value))
            return [LdapPerson(result) for result in ldap_results]
        except KeyError as e:
            raise RecordLoadError("LDAP data source missing")
        except Exception as e:
            print repr(e)
            raise RecordLoadError("LDAP error: %s" % repr(e))

class RedminePerson(object):
    
    def __init__(self,data=None):
        self.data = data or dict()
        self.data['name'] = self.data.get('givenname',[''])[0]+' '+self.data.get('sn',[''])[0]
        
    @classmethod
    def getRecords(self,where,args):
        try:
            mysql = settings['mysql'].connect()
            mysql_results = mysql.query( """
                    SELECT
                        users.id as id,
                        users.login as uid,
                        users.firstname as givenname,
                        users.lastname as sn,
                        roles.name AS role,
                        members.created_on AS since,
                        projects.name AS name
                    FROM users
                        JOIN members ON users.id=members.user_id
                        JOIN roles ON members.role_id=roles.id
                        JOIN projects ON members.project_id=projects.id
                    WHERE
                        %s""" % where, args )
            
            person = dict()
            project = dict()
            for row in mysql_results:
                person[row['id']] = dict(
                        uid=row['uid'],
                        given=row['givenname'],
                        sn=row['sn'],
                        projects=set(),
                    )
                project[row['name']] = dict(
                        name=row['name'],
                        role=row['role'],
                        since=row['since'],
                    )
            for row in mysql_results:
                person[row['id']]['projects'].add(row['name'])
                
            for uid,value in person.items():
                value['projects'] = [project[name] for name in value['projects']]
                
            return [RedminePerson(data) for data in person.values()]
            
        except KeyError as e:
            raise RecordLoadError("Mysql data source missing")
        except Exception as e:
            raise RecordLoadError("Mysql error: %s" % repr(e))
        
class CouchPerson(object):
    
    def __init__(self,result=None):
        self.data = result.value if result else dict()
        
    @classmethod
    def getRecords(self,view,key):
        try:
        
            couch = settings['couch'].connect()
            couch_results = filter(lambda x: x.key==key, couch.view('main/%s' % view))
            return [CouchPerson(result) for result in couch_results]
            
        except KeyError as e:
            raise RecordLoadError("Couch data source missing")
        except Exception as e:
            print repr(e)
            raise RecordLoadError("Couch error: %s" % repr(e))
        
class Person(object):            
            
    def __init__(self,data=None):
        self.data = data or dict()
        
    def __getitem__(self,name):
        if hasattr(self,name):
            return getattr(self,name)
        elif name in self.data:
            return self.data[name]
        raise KeyError("No such attribute '%s' for person" % name)
    
    def __getattr__(self,name):
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError(name)
            
    def get(self,name,default=None):
        if hasattr(self,name):
            return getattr(self,name)
        else:
            return default
    
    def save(self):
        if self.id in settings['couch']:
            doc = settings['couch'][self.id]
            for key,value in self.__dict__.iteritems():
                doc[key] = value
            settings['couch'][self.id] = doc
        else:
            settings['couch'][self.id]=self.__dict__
            
    def set_avatar(self,avatar):
        filename = '%s.%s' % (self.name.remove(' ',''),avatar['filename'].rsplit('.')[-1])
        self.data['avatar'] = settings['avatars']+filename
        with open(settings['server_root']+'static/'+self.data['avatar'],'w') as outfile:
            outfile.write(avatar['body'])        
    
def fromId(uid):
    results = list()
    uid = urllib.unquote_plus(uid)
    print "Person.fromId( %s )" % uid
        
    try:
        results.extend(CouchPerson.getRecords('by_uid',uid))
    except RecordLoadError as e:
        print repr(e)
        
    try:
        results.extend(RedminePerson.getRecords('login=%s',[uid]))
    except RecordLoadError as e:
        print repr(e)
        
    try:
        results.extend(LdapPerson.getRecords('uid',uid))
    except RecordLoadError as e:
        print repr(e)
        
    return reducePeople(results)
        
def fromName(name):
    results = list()
    name = urllib.unquote_plus(name)
    print "Person.fromName( %s )" % name
        
    try:
        results.extend(CouchPerson.getRecords('by_name',name))
    except RecordLoadError as e:
        print repr(e)
        
    try:
        parts = name.split()
        results.extend(RedminePerson.getRecords('firstname=%s and lastname=%s',(parts[0],parts[-1])))
    except RecordLoadError as e:
        print repr(e)
    
    try:
        results.extend(LdapPerson.getRecords('cn',name))
    except RecordLoadError as e:
        print repr(e)
        
    return reducePeople(results)
    
def reducePeople(people):
    people = people or []
    print "Reducing %i people" % len(people)
    persons = dict()
    
    for person in people:
        uid = person.data['uid']
        if uid not in persons:
            persons[uid] = Person()
        persons[uid].data.update(person.data)
        
    return persons.values()
    
def authenticate(who,cred):
    return settings['ldap'].simple_auth(who,cred)
    
def getNameFromUID(who):
    return settings['ldap'].get("(uid=%s)" % who)[1]['cn'][0]
    
if __name__ == '__main__':
    from pprint import PrettyPrinter
    pprint = PrettyPrinter(indent=2).pprint
    
    pprint(fromName('Ann Shaw'))
