#!/usr/bin/env python
#coding:utf-8
# Author:   AIFDR www.aifdr.org
# Purpose:  Act as the Riab API
# Created: 01/16/2011

import os, string
from geoserver_api import geoserver

class RiabAPI():
    API_VERSION='0.1a'
        
    def version(self):
        return self.API_VERSION
    
    
    def create_geoserver_layer_handle(self, username, userpass, geoserver_url, layer_name, workspace):
        """Create fully qualified geoserver layer name
        
        Arguments
            username=username
            userpass=password 
            geoserver_url=The URL of the geoserver   
            layer_name=name of data layer
            workspace=name of geoserver workspace (default is None)
            
            
        Returns
            layer_handle=string of the form:
                username:password@geoserver_url/[workspace/]layer_name
                
        Example         
            admin:geoserver@http://localhost:8080/geoserver/hazard/shakemap_padang_20090930
                 

                     
        """
        if workspace == '':
            return '%s:%s@%s/%s' % (username, userpass, geoserver_url, layer_name)
        else:
            return '%s:%s@%s/[%s]/%s' % (username, userpass, geoserver_url, workspace, layer_name)        

        
    def split_geoserver_layer_handle(self, geoserver_layer_handle):
        """Split fully qualified geoserver layer name into its constituents
        
        Arguments
            geoserver_layer_handle=string with format: 
                username:password@geoserver_url/[hazard]/shakemap_padang_20090930
            or
                username:password@geoserver_url/shakemap_padang_20090930            
                
                
            geoserver_url may optionally start with 'http://'
        """
        
        # Check that handle is well formed
        msg = 'Geoserver layer handle must have the form username:password@geoserver_url/[workspace]/layer_name. '
        msg += 'I got %s' % geoserver_layer_handle
        assert geoserver_layer_handle.find('@') > 0, msg
        assert geoserver_layer_handle.find(':') > 0, msg        
        assert geoserver_layer_handle.find('/') > 0, msg                
        
        
        # Separate username, password and everything following '@'
        userpass, gurl = geoserver_layer_handle.split('@')
        username, password = userpass.split(':')
        
        # Take care of optional http://, https:// etc
        i = gurl.find('://')
        split_index = i+3
        if i > 0: 
            url_prefix = gurl[:split_index]
            gurl = gurl[split_index:]
        else:
            url_prefix = ''
            
        # Split and get layername as last field    
        dirs = gurl.split('/')
        layer_name = dirs.pop()                            
                        
        # Take care of optional workspace enclosed in [..]    
        i = gurl.find('/[')
        j = gurl.find(']/')
        if i > 0 and j > i:
            workspace = dirs.pop()[1:-1] # Strip brackets ([ and ])            
        else:
            workspace = ''             # No workspace in string
            
        # Join remaining fields to form URL
        geoserver_url = url_prefix + string.join(dirs, '/')

        # Return    
        return username, password, geoserver_url, layer_name, workspace
    
    
    def check_geoserver_layer_handle(self, geoserver_layer_handle):
        """Check geoserver layer name
        
        Verify that layer name exists and can be accessed.
        
        Arguments
            geoserver_layer_handle = fully qualified geoserver layer name 
            
        Returns
            'SUCCESS' if complete
            'ERROR: CANNOT CONNECT TO GEOSERVER %s - ERROR MESSAGE IS %s' 
                    
        """
        username, userpass, geoserver_url, layer_name, workspace = self.split_geoserver_layer_handle(geoserver_layer_handle)
        
        try:
            geoserver.Geoserver(geoserver_url, username, userpass)      
        except Exception, msg:
            return 'ERROR: CANNOT CONNECT TO GEOSERVER %s - ERROR MESSAGE IS %s' % (geoserver_layer_handle,msg) 
        else:
            return 'SUCCESS'

            
    def create_workspace(self, username, userpass, geoserver_url, workspace_name):
        """Create new workspace on GeoServer
        
        Arguments
            username=username
            userpass=password 
            geoserver_url=The URL of the geoserver   
            workspace=name of new geoserver workspace
            
        Returns
            'SUCCESS' if complete
            'ERROR: CANNOT CREATE WORKSPACE %s ON GEOSERVER %s - ERROR MESSAGE IS %s' 

        """
        # FIXME(Ole): This does not work with the general layer handle. Perhaps reconsider general handle syntax.
        
        if self.workspace_exists(username, userpass, geoserver_url, workspace_name):
            # If it already exists, return silently
            return
        
        # Connect to Geoserver
        gs = geoserver.Geoserver(geoserver_url, username, userpass)                  
        gs.create_workspace(workspace_name, verbose=False)
                    
        # Check that it was indeed created 
        if not self.workspace_exists(username, userpass, geoserver_url, workspace_name):
            msg = 'Workspace %s was not created succesfully on geoserver %s' % (workspace_name, geoserver_url)
            raise Exception(msg)
                    
    def workspace_exists(self, username, userpass, geoserver_url, workspace_name):
        """Check that workspace exists on geoserver
        
        Arguments
            username=username
            userpass=password 
            geoserver_url=The URL of the geoserver   
            workspace=name of geoserver workspace        
            
        Returns
            True or False
        """
        
        gs = geoserver.Geoserver(geoserver_url, username, userpass)                  
        try:
            gs.get_workspace(workspace_name, verbose=False)
        except:
            return False
        else:
            return True
        
    
    def calculate(self, hazards, exposures, impact_function_id, impact, comment):
        """Calculate the Impact Geo as a function of Hazards and Exposures
        
        Arguments
            impact_function_id=Id of the impact function to be run 
                               (fully qualified path (from base path))
            hazards = An array of hazard levels .. [H1,H2..HN] each H is a geoserver layer path 
                      where each layer follows the format 
                      username:userpass@geoserver_url:layer_name 
                      (Look at REST for inspiration)
            exposure = An array of exposure levels ..[E1,E2...EN] each E is a 
                       geoserver layer path
            impact = The output impact level
            comment = String with comment for output metadata
        
        Returns
            string: 'SUCCESS' if complete
                    'ERROR: PROCESSING %s' : An error has occurred during processing
                    'ERROR: INVALID IMPACT FUNCTION %s' : impact function does not support the hazard and/or exposure type
                    'ERROR: GEOSERVER %s': Failed to connect to the geoserver
                    'WARNING: PROJECTION UNKNOWN %s': A layer does not have projection information
                     error-string if fail
        """
        return 'ERROR: NO IMPLEMENTATION'
    
    
    def suggest_impact_func_ids(self, hazards, exposures):
        """Return appropriate impact function ids for the given hazards and exposure
        
        Arguments
            hazards = An array of hazard levels .. [H1,H2..HN] each H is a geoserver layer path
            exposure = An array of exposure levels ..[E1,E2...EN] each E is a geoserver layer path
        
        Returns
            impact_function_ids = array of ids of the impact function that can be run
        """
        return 'ERROR: NO IMPLEMENTATION'

            
    def get_impact_func_details(self, impact_function_id):
        """Return appropriate impact function details for the given hazards and exposure
        
        Arguments
            impact_function_id = id of the impact function
        
        Returns
            a hash containing details of the impact function:
            mandatory fields are: 'Name', 'Description', 'Author'
        """
        return 'ERROR: NO IMPLEMENTATION'
    
    
    def get_all_impact_functions(self):
        """Return a list of all impact functions 
        
        Arguments
            impact_function_id = id of the impact function
        
        Returns
            a hash containing details of the impact function:
            mandatory fields are: 'Name', 'Description', 'Author'
        """
        return 'ERROR: NO IMPLEMENTATION'
    
    
    #----------------------
    # GeoServer Interfacing
    #----------------------    

    def upload_geoserver_layer(self, data, name):
        """Upload (raster or vector) data to the specified geoserver
        
        Arguments
            data = the layer data
            name = the fully qualified geoserver layer name
        
        Returns
            'SUCCESS' or 'ERROR: ....'
        
        """

        # FIXME(Ole): Currently, this will ignore the layername in the handle and derive it from the filename
        

        username, userpass, geoserver_url, layer_name, workspace = self.split_geoserver_layer_handle(name)

        # FIXME: Check that workspace exists!
                
        try:        
            gs = geoserver.Geoserver(geoserver_url, username, userpass)                                  
        except Exception, msg:
            return 'ERROR: Could not connect to geoserver %s: %s' % (geoserver_url, msg)

        try:    
            gs.upload_layer(filename=data, workspace=workspace, verbose=False)
        except Exception, msg:
            return 'ERROR: Could not upload file %s to geoserver %s: %s' % (data, geoserver_url, msg)     
            
        
        return 'SUCCESS'

    
    def download_geoserver_raster_layer(self, name, bounding_box=None):
        """Upload data to the specified geoserver
        
        Keyword arguments
            name = the fully qualified name of the layer i.e. 'username:password@geoserver_url:shakemap_padang_20090930'
            bounding box = array bounds of the downloaded map e.g [96.956,-5.519,104.641,2.289] (default None, in which case all data is returned)
          
        
        Returns
            layerdata = the layer data as a tif, error string if there are any errors
        
        Note: Exceptions are expected to propagate through XMLRPC 
        """
        return 'ERROR: NO IMPLEMENTATION'
    
    
    def download_geoserver_vector_layer(self):
        """Download data to the specified geoserver
        
        Note - can this be wrapped up with the raster version? 
        """
        return 'ERROR: NO IMPLEMENTATION'
    
