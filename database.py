#!/usr/bin/python

import couchdb
from couchdb.design import *

class Database(object):

    def __init__(self,url,name,**kwargs):
        """ Add all the keyword arguments as object properties
            requires that the url and name keywords be set
        """
        self.__dict__.update(kwargs.items()+[['url',url],['name',name]])
        
    def connect(self):
        
        #Connect to the server
        couch = couchdb.Server(self.url)
        
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

if __name__ == '__main__':
    
    database = Database(url='http://localhost:5984',name='nyss_senbook')
