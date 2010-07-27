#!/usr/bin/python

################################################################################

import couchdb
from couchdb.design import *

class Couch(object):

    def __init__(self,host,name,**kwargs):
        """ Add all the keyword arguments as object properties
            requires that the url and name keywords be set """
        self.host=host
        self.name=name
        self.__dict__.update(kwargs)
        self.configure(self)
        
    def connect(self):
        
        #Connect to the server
        couch = couchdb.Server(self.host)
        
        #Get existing database or create a new one
        if self.name not in couch:
            self.db = couch.create(self.name) 
        else:
            self.db = couch[self.name]
        
        return self.db

    def configure(self):
        ''' define/update the views. note that the sync function will
        also update existing views.'''

        self.connect()
        #Define the views here
        
        return self


################################################################################

from MySQLdb import connect
from MySQLdb.cursors DictCursor

class MySQL(object):

    def __init__(self,host,user,password,db,**kwargs):
        self.host=host
        self.user=user
        self.password=password
        self.db=db
        self.__dict__.update(kwargs)

################################################################################

import ldap

class Ldap(object):
    
    def_filterstr = "(objectClass=*)"
    methods = ['simple','sasl']
    
    def __init__(self,url,**kwargs):
        defaults = dict( who='',cred='',method='simple' )
        options = dict(defaults.items()+kwargs.items()+[['url',url]])
        
        if options['method'] not in ['simple','sasl']:
            msg = "Invalid method '%s'. Method must be 'simple' or 'sasl'."
            raise ValueError( msg % options['method'])
        
        self.__dict__.update(options)
        
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

