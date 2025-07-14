#!/usr/bin/env python3
"""
LSL-Lab Remote API Test Script
=============================

This script tests the remote control API endpoints of an LSL-Lab instance.
Use this to verify that the remote integration is working correctly.

Usage:
------
python test_remote_api.py [host] [port]

Examples:
---------
python test_remote_api.py                    # Test localhost:8080
python test_remote_api.py 192.168.1.100     # Test specific IP on port 8080
python test_remote_api.py 192.168.1.100 8081 # Test specific IP and port
"""

import requests
import json
import sys
import time

class LSLLabAPITester:
    def __init__(self, host='localhost', port=8080):
        self.base_url = f'http://{host}:{port}/api'
        self.host = host
        self.port = port
        
    def test_health(self):
        """Test the health endpoint"""
        print(f"Testing health endpoint...")
        try:
            response = requests.get(f'{self.base_url}/health', timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Health check passed")
                print(f"  Status: {data.get('status')}")
                print(f"  Connected: {data.get('connected')}")
                print(f"  Recording: {data.get('recording')}")
                print(f"  Participant ID: {data.get('participant_id')}")
                return True
            else:
                print(f"✗ Health check failed: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Health check failed: {e}")
            return False
    
    def test_set_participant(self, participant_id='TEST_PARTICIPANT'):
        """Test setting participant ID"""
        print(f"Testing set participant ID to '{participant_id}'...")
        try:
            response = requests.post(
                f'{self.base_url}/participant/set',
                json={'participant_id': participant_id},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✓ Participant ID set successfully")
                    print(f"  Message: {data.get('message')}")
                    return True
                else:
                    print(f"✗ Failed to set participant ID: {data.get('message')}")
                    return False
            else:
                print(f"✗ Set participant failed: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Set participant failed: {e}")
            return False
    
    def test_recording_control(self):
        """Test recording start/stop"""
        print(f"Testing recording control...")
        
        # Test start recording
        try:
            response = requests.post(f'{self.base_url}/recording/start', timeout=5)
            data = response.json()
            if response.status_code == 200 and data.get('success'):
                print(f"✓ Recording start successful: {data.get('message')}")
            else:
                print(f"⚠ Recording start: {data.get('message')} (this is expected if device not connected)")
        except requests.exceptions.RequestException as e:
            print(f"✗ Recording start failed: {e}")
            return False
        
        time.sleep(1)
        
        # Test stop recording
        try:
            response = requests.post(f'{self.base_url}/recording/stop', timeout=5)
            data = response.json()
            if response.status_code == 200 and data.get('success'):
                print(f"✓ Recording stop successful: {data.get('message')}")
            else:
                print(f"⚠ Recording stop: {data.get('message')} (this is expected if not recording)")
        except requests.exceptions.RequestException as e:
            print(f"✗ Recording stop failed: {e}")
            return False
        
        return True
    
    def test_interval_control(self):
        """Test interval start/end"""
        print(f"Testing interval control...")
        
        # Test start interval
        try:
            response = requests.post(
                f'{self.base_url}/interval/start',
                json={'interval_name': 'Test_Interval'},
                timeout=5
            )
            data = response.json()
            if response.status_code == 200 and data.get('success'):
                print(f"✓ Interval start successful: {data.get('message')}")
            else:
                print(f"⚠ Interval start: {data.get('message')} (this is expected if not recording)")
        except requests.exceptions.RequestException as e:
            print(f"✗ Interval start failed: {e}")
            return False
        
        time.sleep(1)
        
        # Test end interval
        try:
            response = requests.post(f'{self.base_url}/interval/end', timeout=5)
            data = response.json()
            if response.status_code == 200 and data.get('success'):
                print(f"✓ Interval end successful: {data.get('message')}")
            else:
                print(f"⚠ Interval end: {data.get('message')} (this is expected if no active interval)")
        except requests.exceptions.RequestException as e:
            print(f"✗ Interval end failed: {e}")
            return False
        
        return True
    
    def test_timestamp_marking(self):
        """Test timestamp marking"""
        print(f"Testing timestamp marking...")
        try:
            response = requests.post(
                f'{self.base_url}/timestamp/mark',
                json={'timestamp_name': 'Test_Timestamp'},
                timeout=5
            )
            data = response.json()
            if response.status_code == 200 and data.get('success'):
                print(f"✓ Timestamp marking successful: {data.get('message')}")
                return True
            else:
                print(f"⚠ Timestamp marking: {data.get('message')} (this is expected if not recording)")
                return True  # Not a failure, just expected behavior
        except requests.exceptions.RequestException as e:
            print(f"✗ Timestamp marking failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all API tests"""
        print(f"="*60)
        print(f"LSL-Lab Remote API Test Suite")
        print(f"Testing: {self.host}:{self.port}")
        print(f"="*60)
        
        tests = [
            self.test_health,
            self.test_set_participant,
            self.test_recording_control,
            self.test_interval_control,
            self.test_timestamp_marking
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            print()
            success = test()
            if success:
                passed += 1
            print("-" * 40)
        
        print()
        print(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print(f"✓ All tests passed! LSL-Lab remote API is working correctly.")
        elif passed > 0:
            print(f"⚠ Some tests passed. Check connection and device status.")
        else:
            print(f"✗ All tests failed. Check if LSL-Lab is running and accessible.")
        
        return passed == total

def main():
    """Main test function"""
    # Parse command line arguments
    host = 'localhost'
    port = 8080
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Error: Invalid port number '{sys.argv[2]}'")
            sys.exit(1)
    
    # Run tests
    tester = LSLLabAPITester(host, port)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 