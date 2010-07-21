import ldap
import settings

class ldapter(object):
    
    methods = ['simple','sasl']
    def __init__(self,url,**kwargs):
        defaults = dict( who='',cred='',method='simple' )
        options = dict(defaults.items()+kwargs.items())
        
        if options['method'] not in self.methods:
            raise ValueError(msg % (options['method'],self.methods))
            
        self.__dict__.update(options.items()+[['url',url]])
        
    def search(self,filterstr="(objectClass=*)",**kwargs):
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

    def connect(self):
        
        self.server = ldap.initialize(self.url)
        if self.method == 'simple':
            self.server.simple_bind_s(self.who,self.cred)
        elif self.method == 'sasl':
            raise NotImplementedError("SASL authentication not yet implemented")
        
        return self
        
if __name__ == '__main__':
    
    ldap_config = dict(
        url='ldap://webmail.senate.state.ny.us/',
        who='',
        cred='',
        auth='simple', #Allowed values are ['simple','sasl']
        )
        
    l = ldapter(**ldap_config)
