from settings import settings
from people import LdapPerson

class RecordLoadError(Exception):
    pass

class LdapGroup(object):

    def __init__(self,result):
        cn, self.data = result
        self.data['name'] = self.data['displayname'][0]
        
    @classmethod
    def getRecords(self,name,full=True):
        try:
            ldap = settings['ldap'].connect()
            
            filterstr = '(&(cn=%s)(objectClass=dominoGroup)(giddisplay=Public))' % name
            results = ldap.search(filterstr)
            
            def cleanMember(member):
                return '(cn=%s)' % member.split('=')[1].split(',')[0]
            def cleanResult(result):
                return cleanMember(result[0])
                
            if full:
                for cn,result in results:
                    result['members'] = list()
                    members = set(map(cleanMember,result['member']))
                    print len(members)
                    filterstr = '(&(|%s)(objectClass=dominoPerson))'
                    ldap_results = ldap.search(filterstr % ''.join(members),all=1)
                    print "(%s) Person Results" % len(ldap_results)
                    if ldap_results:
                        result['members'].extend([LdapPerson(ldap_result) for ldap_result in ldap_results])
                        members = members - set(map(cleanResult,ldap_results))
                    print len(members)
                    if len(members):
                        filterstr = '(&(|%s)(objectClass=dominoGroup))'
                        ldap_results = ldap.search(filterstr % ''.join(members))
                        print "(%s) Group Results" % len(ldap_results)
                        if ldap_results:
                            result['members'].extend([LdapGroup(ldap_result) for ldap_result in ldap_results])
                            
            return [LdapGroup(result) for result in results]
        except RecordLoadError as e:
            pass

    def __getattr__(self,name):
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError(name)
            
    def __getitem__(self,name):
        if hasattr(self,name):
            return getattr(self,name)
        elif name in self.data:
            return self.data[name]
        raise KeyError("No such attribute '%s' for group" % name)

class Group(object):
    
    def __init__(self,data=None):
        self.data = data or dict()
        
    def __getattr__(self,name):
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError(name)
            
    def __getitem__(self,name):
        if hasattr(self,name):
            return getattr(self,name)
        elif name in self.data:
            return self.data[name]
        raise KeyError("No such attribute '%s' for group" % name)

def fromName(name):
    results = list()
    
    try:
        results.extend(LdapGroup.getRecords(name))
    except RecordLoadError as e:
        print repr(e)
    
    return reduceGroups(results)

def reduceGroups(groups):
    groups = groups or []
    print "Reducing %i groups" % len(groups)
    print groups
    results = dict()
    
    for group in groups:
        name = group.data['name']
        if name not in results:
            results[name] = Group()
        results[name].data.update(group.data)
        
    return results.values()
