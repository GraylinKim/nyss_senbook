import ldap
import settings

class ldapter(object):
    
    def_filterstr = "(objectClass=*)"
    methods = ['simple','sasl']
    
    def __init__(self,url,**kwargs):
        defaults = dict( who='',cred='',method='simple' )
        options = dict(defaults.items()+kwargs.items())
        
        if options['method'] not in self.methods:
            raise ValueError(msg % (options['method'],self.methods))
            
        self.__dict__.update(options.items()+[['url',url]])
        
    def search(self,filterstr=def_filterstr,**kwargs):
        options = dict(self.__dict__.items()+kwargs.items())
        base = options.get('base',"")
        scope = options.get('scope',ldap.SCOPE_SUBTREE)
        filterstr = filterstr
        attrlist = options.get('attrlist',None)
        attrsonly = options.get('attrsonly',0)
        timeout = options.get('timeout', -1)
        all = options.get('all',0)
        
        search_id = self.server.search(base,scope,filterstr,attrlist,attrsonly)
        result_type = 0
        
        result_type = -1
        while result_type != ldap.RES_SEARCH_RESULT:
            result_type, result_data = self.server.result(search_id, all=all,timeout=timeout)
            for result in result_data:
                yield result
    
    def get(self,filterstr=def_filterstr,**kwargs):
        return self.search(filterstr,**kwargs).next()
            
    def connect(self):
        
        self.server = ldap.initialize(self.url)
        if self.method == 'simple':
            self.server.simple_bind_s(self.who,self.cred)
        elif self.method == 'sasl':
            raise NotImplementedError("SASL authentication not yet implemented")
        
        return self
        
    def simple_auth(self,who,cred):
        try:
            self.server = ldap.initialize(self.url)
            self.server.simple_bind_s(who,cred)
            return True
        except ldap.InvalidCredentials as e:
            return False
            
if __name__ == '__main__':
    
    ldap_config = dict(
        url='ldap://webmail.senate.state.ny.us/',
        who='',
        cred='',
        auth='simple', #Allowed values are ['simple','sasl']
        )
        
    l = ldapter(**ldap_config)
