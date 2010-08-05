from settings import settings

class Group(object):
    
    def __init__(self,name):
        server = settings['ldap'].connect()
        filterstr = '(&(cn=%s)(objectClass=dominoGroup))' % name
        results = server.search(filterstr)
        print "RESULTS %s" % results
        self.id, self.data = results[0]
        
    def __getitem__(self,name):
        if hasattr(self,name):
            return getattr(self,name)
        elif name in self.data:
            return self.data[name]
        raise KeyError("No such attribute '%s' for person" % name)
