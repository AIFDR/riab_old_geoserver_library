#!/usr/bin/env python

import os
import sys
import numpy
import unittest
import pycurl, StringIO, json
from config import test_workspace_name, geoserver_url, geoserver_username, geoserver_userpass
        

from utilities import get_web_page

# Add location of source code to search path so that API can be imported
parent_dir = os.path.split(os.getcwd())[0]
source_path = os.path.join(parent_dir, 'source') 
sys.path.append(source_path)

# Import everything from the API
from riab_api import *


class Test_API(unittest.TestCase):

    def setUp(self):
        self.api = RiabAPI()
            
    def tearDown(self):
        pass

        
    def test_create_geoserver_handles_1(self):
        """Test that handles without workspace are created correctly
        """

        s = self.api.create_geoserver_layer_handle('ted', 'test', 'www.geo.com', 'map', '')
        msg = 'Wrong handle returned %s' % s
        assert s == 'ted:test@www.geo.com/map', msg
        
        
    def test_create_geoserver_handles_2(self):
        """Test that handles with workspace and port are created correctly
        """
        
        username = 'alice'
        userpass = 'cooper'
        layer_name = 'poison'
        geoserver_url = 'schools.out.forever:88'
        workspace = 'black'        

        s = self.api.create_geoserver_layer_handle(username, 
                                                   userpass, 
                                                   geoserver_url, 
                                                   layer_name, 
                                                   workspace)                    
            
        msg = 'Wrong handle returned %s' % s
        assert s == 'alice:cooper@schools.out.forever:88/[black]/poison', msg        
         
    def test_geoserver_layer_handles_3(self):
        """Test that layer handles are correctly formed and unpacked again"""
        
        # Test with and without workspaces as well as with and without port and html prefix
        username='alice'
        userpass='cooper'
         
        for layer_name in ['poison', '']:
            for port in ['', ':88']:
                for prefix in ['', 'html://']:
                    geoserver_url = prefix + 'schools.out.forever' + port
                
                    for workspace in ['black', '']:
                
                        s = self.api.create_geoserver_layer_handle(username, 
                                                                   userpass, 
                                                                   geoserver_url, 
                                                                   layer_name, 
                                                                   workspace)

                        s1, s2, s3, s4, s5 = self.api.split_geoserver_layer_handle(s)
                        assert s1 == username
                        assert s2 == userpass
                        assert s3 == geoserver_url
                        assert s4 == layer_name
                        assert s5 == workspace
                    

    def test_another_layer_handle_unpack_example(self):
        """Test unpack of admin:geoserver@http://localhost:8080/geoserver/[topp]/tasmania_roads           
        """
        
        layer_handle = 'admin:geoserver@http://localhost:8080/geoserver/[topp]/tasmania_roads'
        s1, s2, s3, s4, s5 = self.api.split_geoserver_layer_handle(layer_handle)
        
        assert s1 == 'admin'
        assert s2 == 'geoserver'
        assert s3 == 'http://localhost:8080/geoserver'
        assert s4 == 'tasmania_roads'
        assert s5 == 'topp'
        

    def test_connection_to_geoserver(self):
        """Test that geoserver can be reached using layer handle"""
        
        # FIXME(Ole): I think these should be defaults e.g. in config.py
        geoserver_url = 'http://localhost:8080/geoserver'
        username = 'admin'
        userpass = 'geoserver'
        layer_name = 'tasmania_roads'
        workspace = 'topp'        

        lh = self.api.create_geoserver_layer_handle(username, userpass, geoserver_url, layer_name,
                                                    workspace)
        res = self.api.check_geoserver_layer_handle(lh) 
        
        msg = 'Was not able to access Geoserver layer %s: %s' % (lh, res)
        assert res == 'SUCCESS', msg               

        
    def test_create_workspace(self):            
        """Test that new workspace can be created
        """
        
        # Create workspace
        self.api.create_workspace(geoserver_username, geoserver_userpass, geoserver_url, test_workspace_name)
        
        # Check that workspace is there
        found = False
        page = get_web_page(os.path.join(geoserver_url, 'rest/workspaces'), 
                            username=geoserver_username, 
                            password=geoserver_userpass)
        for line in page:
            if line.find('rest/workspaces/%s.html' % test_workspace_name) > 0:
                found = True

        msg = 'Workspace %s was not found in %s' % (test_workspace_name, geoserver_url)        
        assert found, msg


    def test_upload_coverage(self):
        """Test that a coverage can be uploaded and a new style is created
        """
        
        # Create workspace
        self.api.create_workspace(geoserver_username, geoserver_userpass, geoserver_url, test_workspace_name)        
        
        # setup layer, file, sld and style names
        layername = 'shakemap_padang_20090930'
        raster_file = 'data/%s.asc' % layername
        expected_output_sld_file = '%s.sld' % layername 
        stylename = layername 
        
        # Form layer handle
        lh = self.api.create_geoserver_layer_handle(geoserver_username, 
                                                    geoserver_userpass, 
                                                    geoserver_url, 
                                                    '',   # Empty layer means derive from filename
                                                    test_workspace_name)
                
        # Upload coverage
        res = self.api.upload_geoserver_layer(raster_file, lh)
        assert res.startswith('SUCCESS'), res        

        # Check that layer is there
        found = False
        page = get_web_page(os.path.join(geoserver_url, 'rest/layers'), 
                            username=geoserver_username, 
                            password=geoserver_userpass)
        for line in page:
            if line.find('rest/layers/%s.html' % layername) > 0:
                found = True
        
        msg = 'Did not find layer %s in geoserver %s' % (layername, geoserver_url)
        assert found, msg        
        

        # Test style by grabbing the json
        c = pycurl.Curl()
        url = ((geoserver_url+'/rest/layers/%s') % layername)
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.HTTPHEADER, ['Accept: text/json'])
        c.setopt(pycurl.USERPWD, '%s:%s' % (geoserver_username, geoserver_userpass))
        c.setopt(pycurl.VERBOSE, 0)
        b = StringIO.StringIO()
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        c.perform()

        try:
            d = json.loads(b.getvalue())
            def_style = d['layer']['defaultStyle']['name']
        except:
            def_style = b.getvalue()
            
        msg =   'Expected: '+stylename
        msg +=   'Got: '+def_style+"\n"
        assert def_style == stylename, msg
        
        # FIXME (Ole): This fails as no style appears in REST interface. Why?
        # Check that style appears on the geoserver
        #found = False
        #page = get_web_page(os.path.join(geoserver_url, 'rest/styles'), 
        #                    username=geoserver_username, 
        #                    password=geoserver_userpass)
        #for line in page:
        #    if line.find('rest/styles/%s.html' % layername) > 0:
        #        found = True
        # 
        #msg = 'Style %s was not found in %s' % (layername, geoserver_url)        
        #assert found, msg

        
        
    def test_upload_of_coverage_without_coordinate_system(self):
        """Test that upload of coverage without coordinate system raises an error"""
        
        # Create workspace
        self.api.create_workspace(geoserver_username, geoserver_userpass, geoserver_url, test_workspace_name)        
        
        # setup layer, file, sld and style names
        layername = 'missing_prj_shakemap_padang_20090930.tif'
        raster_file = 'data/%s' % layername
        
        # Form layer handle
        lh = self.api.create_geoserver_layer_handle(geoserver_username, 
                                                    geoserver_userpass, 
                                                    geoserver_url, 
                                                    '',   # Empty layer means derive from filename
                                                    test_workspace_name)
        

        # Upload coverage
        try:
            res = self.api.upload_geoserver_layer(raster_file, lh)
        except:
            # FIXME(Ole): Define custom exception in riab_api for this condition.
            # Exception raised as planned
            pass
        else:
            msg = 'Exception should have been raised when layer has no projection file'
            raise Exception(msg)
        

        
    def test_upload_coverage2(self):
        """Test that a coverage (with extension .txt) can be uploaded and a new style is created
        """
        # FIXME: (Shoaib) Breaking for me with following log message: 
        # 10 Aug 20:07:12 INFO [catalog.rest] - PUT file, mimetype: image/tif
        # 10 Aug 20:07:12 INFO [catalog.rest] - Using existing coverage store: mmi_lembang_68
        # 10 Aug 20:07:12 WARN [gce.geotiff] - I/O error reading image metadata!
        # Looks like its loading it as a geoserver - geoserver goes half way to creating the 
        # new resource: so it creates a coveragestore and coverage but not layer 
        # Weird (Ole): It works on my systems (Ubuntu 9.04 and 10.04)
        
        layername = 'mmi_lembang_68'
        raster_file = 'data/%s.txt' % layername
        expected_output_sld_file = '%s.sld' % layername 
        stylename = layername 

        # Create workspace
        self.api.create_workspace(geoserver_username, geoserver_userpass, geoserver_url, test_workspace_name)
        
        # Form layer handle
        lh = self.api.create_geoserver_layer_handle(geoserver_username, 
                                                    geoserver_userpass, 
                                                    geoserver_url, 
                                                    '',   # Empty layer means derive from filename
                                                    test_workspace_name)
        
        # Upload coverage
        res = self.api.upload_geoserver_layer(raster_file, lh)
        assert res.startswith('SUCCESS'), res        
        
        c = pycurl.Curl()
        url = ((geoserver_url+'/rest/layers/%s') % layername)
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.HTTPHEADER, ['Accept: text/json'])
        c.setopt(pycurl.USERPWD, '%s:%s' % (geoserver_username, geoserver_userpass))
        c.setopt(pycurl.VERBOSE, 0)
        b = StringIO.StringIO()
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        c.perform()
        
        try:
            d = json.loads(b.getvalue())
            def_style = d['layer']['defaultStyle']['name']
        except:
            def_style = b.getvalue()
        msg =   'Expected: '+stylename
        msg +=  ' Got: '+def_style+'\n'

        assert def_style == stylename, msg


    def Xtest_download_coverage(self):
        """Test that a coverage can be downloaded
        """
    
        # Upload first to make sure data is there    
        
        self.api.create_workspace(geoserver_username, geoserver_userpass, geoserver_url, test_workspace_name)

        lh = self.api.create_geoserver_layer_handle(geoserver_username, 
                                                    geoserver_userpass, 
                                                    geoserver_url, 
                                                    '',   # Empty layer means derive from filename
                                                    test_workspace_name)

        res = self.api.upload_geoserver_layer('data/shakemap_padang_20090930.asc', lh)
        assert res.startswith('SUCCESS'), res                
                                    
    
        # Apply known bounding box manually read from the Geoserver
        bounding_box = [96.956, -5.519, 104.641, 2.289]
                        
        # Download using the API and test that the data is the same.
        lh = self.api.create_geoserver_layer_handle(geoserver_username, 
                                                    geoserver_userpass, 
                                                    geoserver_url, 
                                                    'shakemap_padang_20090930',
                                                    test_workspace_name)        
        
        downloaded_tif = 'downloaded_shakemap.tif'
        self.api.download_coverage(coverage_name='shakemap_padang_20090930',
                                   bounding_box=bounding_box,
                                   workspace=test_workspace_name,
                                   output_filename=downloaded_tif,
                                   verbose=False)
                                         
        # Verify existence of downloaded file
        msg = 'Downloaded coverage %s does not exist' % downloaded_tif
        assert downloaded_tif in os.listdir('.'), msg
        
        # FIXME: Convert downloaded data to ascii and compare:
        
                                
        
################################################################################

if __name__ == '__main__':
    suite = unittest.makeSuite(Test_API, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
