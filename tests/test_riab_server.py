#!/usr/bin/env python

import sys, os
import unittest
import xmlrpclib
from config import test_url

class Test_Riab_Server(unittest.TestCase):

    have_reloaded = False
    
    def setUp(self):
        """Connect to test geoserver with new instance
        """
            
        self.riab_server = xmlrpclib.ServerProxy(test_url)
        try:
            if not self.have_reloaded:
                s = self.riab_server.reload()
                self.have_reloaded = True
        except:
            print 'Warning can\'t reload classes!'
            
    def tearDown(self):
        """Destroy test geoserver again next test
        """
        
        pass
        

    def test_riab_server_reload(self):
        """Test the reload function
        """
        # make sure the latest classes are being used
        
        s = self.riab_server.reload()
        assert s.startswith('SUCCESS'), 'Problem with the reload'
        
        # Exception will be thrown if there is no server

    def test_riab_server_version(self):
        """Test that local riab server is running
        """
        # make sure the latest classes are being used
        
        s = self.riab_server.version()
        assert s.startswith('0.1a'), 'Version incorrect %s' % s
        
        # Exception will be thrown if there is no server

    
    
    def test_create_geoserver_handles_1(self):
        """Test that handles without workspace are created correctly
        """

        s = self.riab_server.create_geoserver_layer_handle('ted', 'test', 'www.geo.com', 'map', '')
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

        s = self.riab_server.create_geoserver_layer_handle(username, 
                                                           userpass, 
                                                           geoserver_url, 
                                                           layer_name, 
                                                           workspace)                    
            
        msg = 'Wrong handle returned %s' % s
        assert s == 'alice:cooper@schools.out.forever:88/[black]/poison', msg        
         
    def test_geoserver_layer_handles_3(self):
        """Test that layer handles are correctly formed and unpacked again"""
        
        # Test with and without workspaces as well as with and without port
        username='alice'
        userpass='cooper'
        layer_name='poison'
        
        for port in ['', ':88']:
            geoserver_url = 'schools.out.forever' + port
            
            for workspace in ['black', '']:
            
                s = self.riab_server.create_geoserver_layer_handle(username, 
                                                                   userpass, 
                                                                   geoserver_url, 
                                                                   layer_name, 
                                                                   workspace)


                s1, s2, s3, s4, s5 = self.riab_server.split_geoserver_layer_handle(s)
                assert s1 == username
                assert s2 == userpass
                assert s3 == geoserver_url
                assert s4 == layer_name
                assert s5 == workspace
                

    def test_connection_to_geoserver(self):
        """Test that geoserver can be reached using layer handle"""
        
        # FIXME(Ole): I think these should be defaults e.g. in config.py
        geoserver_url = 'http://localhost:8080/geoserver'
        username = 'admin'
        userpass = 'geoserver'
        layer_name = 'tasmania_roads'
        workspace = 'topp'

        s = self.riab_server.create_geoserver_layer_handle(username, userpass, geoserver_url, layer_name, 
                                                           workspace)
        res = self.riab_server.check_geoserver_layer_handle(s)
        
        msg = 'Was not able to access Geoserver layer: %s' % s
        assert res == 'SUCCESS', msg
        

################################################################################

if __name__ == '__main__':
    suite = unittest.makeSuite(Test_Riab_Server, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
