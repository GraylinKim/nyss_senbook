import urllib,copy,hashlib

from settings import settings
from datetime import datetime

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
    def auth(self,who,cred):  
        print "LDAP Authentication on '%s' with '%s'" % (who,cred)
        try:
            import ldap
            server = ldap.initialize(settings['ldap_settings']['url'])
            server.simple_bind_s(who,cred)
            data = settings['ldap'].connect().get("(uid=%s)" % who)[1]
            return data['givenname'][0]+' '+data['sn'][0]
        except ldap.INVALID_CREDENTIALS as e:
            return False
            
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
        self.data['name'] = self.data.get('givenname','')+' '+self.data.get('sn','')
        
    @classmethod
    def auth(self,who,cred):
        print "Redmine Authentication on '%s' with '%s'" % (who,cred)
        mysql = settings['mysql'].connect()
        
        args = (who,hashlib.sha1(cred).hexdigest())
        results  = mysql.query( """ 
                SELECT firstname,lastname 
                FROM users
                WHERE 
                    login=%s AND hashed_password=%s""" , args )
                    
        if results:
            return results[0]['firstname']+' '+results[0]['lastname']
        return False
        
    @classmethod
    def getRecords(self,where,args):
        try:
            mysql = settings['mysql'].connect()
            mysql_results = mysql.query("""
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
                        givenname=row['givenname'],
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
        for project in self.data.get('projects',[]):
            #convert back to date time. this will burn and die in 2038
            project['since'] = datetime.utcfromtimestamp(project['since'])
        
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
    
    def save(self):
        couch = settings['couch'].connect()
        data = copy.deepcopy(self.data)
        for project in data.get('projects',[]):
            #put in unix time to store, will break in 2038
            project['since'] = float(project['since'].strftime('%s'))
        if self.uid in couch:
            doc = couch[self.uid]
            doc.update(data)
            print doc
            couch[self.uid] = doc
        else:
            couch[self.uid]=data
            
    def set_avatar(self,avatar):
        filename = '%s.%s' % (self.uid,avatar['filename'].rsplit('.')[-1])
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
    print people
    persons = dict()
    
    for person in people:
        uid = person.data['uid']
        if uid not in persons:
            persons[uid] = Person()
        persons[uid].data.update(person.data)
        
    return persons.values()
    
def authenticate(who,cred):
    return LdapPerson.auth(who,cred) or RedminePerson.auth(who,cred)
    
def getNameFromUID(who):
    ldap = settings['ldap'].connect()
    return ldap.get("(uid=%s)" % who)[1]['cn'][0]
    
if __name__ == '__main__':
    from pprint import PrettyPrinter
    pprint = PrettyPrinter(indent=2).pprint
    
    pprint(fromName('Ann Shaw'))
