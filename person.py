from settings import settings

class Person(object):
    def __init__(self,name):
        db = settings['db']
        ldap = settings['ldap'].connect()
        
        filterstr = '(&(cn=%s)(objectClass=dominoPerson))' % name
        ident, ldap_data = ldap.get(filterstr)
        
        filterstr = '(&(member=%s)(objectClass=dominoGroup))' % ident
        groups = [result for result in ldap.search(filterstr)]

        couch_data = db.get(ident,dict())
        
        self.id = ident
        self.name = ident.split(',')[0][3:]
        self.data = dict(couch_data.get('data',dict()).items()+ldap_data.items()+[['groups',groups]])
        
    def __getitem__(self,name):
        if hasattr(self,name):
            return getattr(self,name)
        elif name in self.data:
            return self.data[name]
        raise KeyError("No such attribute '%s' for person" % name)
        
    def get(self,name,default=None):
        if hasattr(self,name):
            return getattr(self,name)
        else:
            return default
    
    def save(self):
        if self.id in settings['db']:
            doc = settings['db'][self.id]
            for key,value in self.__dict__.iteritems():
                doc[key] = value
            settings['db'][self.id] = doc
        else:
            settings['db'][self.id]=self.__dict__
