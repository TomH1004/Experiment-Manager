#!/usr/bin/env python3
"""
LSL Remote Controller Module
Handles remote communication with LSL-Lab instances for coordinated recording control.
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class LSLDevice:
    """Represents a remote LSL-Lab device"""
    
    def __init__(self, device_id: str, name: str, ip: str, port: int, participant_id: str):
        self.device_id = device_id
        self.name = name
        self.ip = ip
        self.port = port
        self.participant_id = participant_id
        self.is_connected = False
        self.is_recording = False
        self.last_heartbeat = None
        self.connection_status = "Disconnected"
        self.recording_status = "Stopped"
        self.created_at = datetime.now()
        
    def get_base_url(self) -> str:
        """Get the base URL for API calls"""
        return f"http://{self.ip}:{self.port}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary for JSON serialization"""
        return {
            'device_id': self.device_id,
            'name': self.name,
            'ip': self.ip,
            'port': self.port,
            'participant_id': self.participant_id,
            'is_connected': self.is_connected,
            'is_recording': self.is_recording,
            'connection_status': self.connection_status,
            'recording_status': self.recording_status,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'created_at': self.created_at.isoformat()
        }

class LSLRemoteController:
    """Manages multiple remote LSL-Lab instances"""
    
    def __init__(self):
        self.devices: Dict[str, LSLDevice] = {}
        self.session = None
        self.heartbeat_task = None
        self.heartbeat_interval = 10  # seconds
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5),
            connector=aiohttp.TCPConnector(limit=20)
        )
        # Start heartbeat monitoring
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
                
        if self.session:
            await self.session.close()
            
    def add_device(self, device_id: str, name: str, ip: str, port: int, participant_id: str) -> LSLDevice:
        """Add a new LSL device"""
        device = LSLDevice(device_id, name, ip, port, participant_id)
        self.devices[device_id] = device
        logger.info(f"Added LSL device: {name} ({ip}:{port}) for participant {participant_id}")
        return device
        
    def remove_device(self, device_id: str) -> bool:
        """Remove an LSL device"""
        if device_id in self.devices:
            device = self.devices[device_id]
            del self.devices[device_id]
            logger.info(f"Removed LSL device: {device.name}")
            return True
        return False
        
    def get_device(self, device_id: str) -> Optional[LSLDevice]:
        """Get a device by ID"""
        return self.devices.get(device_id)
        
    def get_all_devices(self) -> List[LSLDevice]:
        """Get all devices"""
        return list(self.devices.values())
        
    async def test_device_connection(self, ip: str, port: int) -> Tuple[bool, str]:
        """Test connection to a device before adding it"""
        try:
            if not self.session:
                return False, "Session not initialized"
                
            url = f"http://{ip}:{port}/api/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'healthy':
                        return True, "Connection successful"
                    else:
                        return False, f"Unexpected response: {data}"
                else:
                    return False, f"HTTP {response.status}: {response.reason}"
                    
        except asyncio.TimeoutError:
            return False, "Connection timeout"
        except aiohttp.ClientError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
            
    async def _heartbeat_loop(self):
        """Background task to monitor device health"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._check_all_devices()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                
    async def _check_all_devices(self):
        """Check health of all devices"""
        if not self.session:
            return
            
        tasks = []
        for device in self.devices.values():
            tasks.append(self._check_device_health(device))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def _check_device_health(self, device: LSLDevice):
        """Check health of a single device"""
        try:
            url = f"{device.get_base_url()}/api/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'healthy':
                        device.is_connected = True
                        device.connection_status = "Connected"
                        device.last_heartbeat = datetime.now()
                    else:
                        device.is_connected = False
                        device.connection_status = "Unhealthy"
                else:
                    device.is_connected = False
                    device.connection_status = f"HTTP {response.status}"
                    
        except Exception as e:
            device.is_connected = False
            device.connection_status = f"Error: {str(e)[:50]}"
            logger.debug(f"Health check failed for {device.name}: {e}")
            
    async def set_participant_id(self, device_id: str, participant_id: str) -> Tuple[bool, str]:
        """Set participant ID on a device"""
        device = self.get_device(device_id)
        if not device:
            return False, "Device not found"
            
        try:
            url = f"{device.get_base_url()}/api/participant/set"
            data = {"participant_id": participant_id}
            
            async with self.session.post(url, json=data) as response:
                result = await response.json()
                if result.get('success'):
                    device.participant_id = participant_id
                    logger.info(f"Set participant ID '{participant_id}' on device {device.name}")
                    return True, "Participant ID set successfully"
                else:
                    return False, result.get('message', 'Unknown error')
                    
        except Exception as e:
            logger.error(f"Error setting participant ID on {device.name}: {e}")
            return False, f"Connection error: {str(e)}"
            
    async def start_recording(self, device_id: str) -> Tuple[bool, str]:
        """Start recording on a device"""
        device = self.get_device(device_id)
        if not device:
            return False, "Device not found"
            
        try:
            url = f"{device.get_base_url()}/api/recording/start"
            
            async with self.session.post(url) as response:
                result = await response.json()
                if result.get('success'):
                    device.is_recording = True
                    device.recording_status = "Recording"
                    logger.info(f"Started recording on device {device.name}")
                    return True, "Recording started successfully"
                else:
                    return False, result.get('message', 'Unknown error')
                    
        except Exception as e:
            logger.error(f"Error starting recording on {device.name}: {e}")
            return False, f"Connection error: {str(e)}"
            
    async def stop_recording(self, device_id: str) -> Tuple[bool, str]:
        """Stop recording on a device"""
        device = self.get_device(device_id)
        if not device:
            return False, "Device not found"
            
        try:
            url = f"{device.get_base_url()}/api/recording/stop"
            
            async with self.session.post(url) as response:
                result = await response.json()
                if result.get('success'):
                    device.is_recording = False
                    device.recording_status = "Stopped"
                    logger.info(f"Stopped recording on device {device.name}")
                    return True, "Recording stopped successfully"
                else:
                    return False, result.get('message', 'Unknown error')
                    
        except Exception as e:
            logger.error(f"Error stopping recording on {device.name}: {e}")
            return False, f"Connection error: {str(e)}"
            
    async def start_interval(self, device_id: str, interval_name: str = None) -> Tuple[bool, str]:
        """Start an interval on a device"""
        device = self.get_device(device_id)
        if not device:
            return False, "Device not found"
            
        try:
            url = f"{device.get_base_url()}/api/interval/start"
            data = {"interval_name": interval_name} if interval_name else {}
            
            async with self.session.post(url, json=data) as response:
                result = await response.json()
                if result.get('success'):
                    logger.info(f"Started interval on device {device.name}" + (f" ({interval_name})" if interval_name else ""))
                    return True, "Interval started successfully"
                else:
                    return False, result.get('message', 'Unknown error')
                    
        except Exception as e:
            logger.error(f"Error starting interval on {device.name}: {e}")
            return False, f"Connection error: {str(e)}"
            
    async def end_interval(self, device_id: str) -> Tuple[bool, str]:
        """End an interval on a device"""
        device = self.get_device(device_id)
        if not device:
            return False, "Device not found"
            
        try:
            url = f"{device.get_base_url()}/api/interval/end"
            
            async with self.session.post(url) as response:
                result = await response.json()
                if result.get('success'):
                    logger.info(f"Ended interval on device {device.name}")
                    return True, "Interval ended successfully"
                else:
                    return False, result.get('message', 'Unknown error')
                    
        except Exception as e:
            logger.error(f"Error ending interval on {device.name}: {e}")
            return False, f"Connection error: {str(e)}"
            
    async def mark_timestamp(self, device_id: str, timestamp_name: str = None) -> Tuple[bool, str]:
        """Mark a timestamp on a device"""
        device = self.get_device(device_id)
        if not device:
            return False, "Device not found"
            
        try:
            url = f"{device.get_base_url()}/api/timestamp/mark"
            data = {"timestamp_name": timestamp_name} if timestamp_name else {}
            
            async with self.session.post(url, json=data) as response:
                result = await response.json()
                if result.get('success'):
                    logger.info(f"Marked timestamp on device {device.name}" + (f" ({timestamp_name})" if timestamp_name else ""))
                    return True, "Timestamp marked successfully"
                else:
                    return False, result.get('message', 'Unknown error')
                    
        except Exception as e:
            logger.error(f"Error marking timestamp on {device.name}: {e}")
            return False, f"Connection error: {str(e)}"
            
    async def start_all_recording(self) -> Tuple[int, int, List[str]]:
        """Start recording on all devices"""
        tasks = []
        for device_id in self.devices.keys():
            tasks.append(self.start_recording(device_id))
            
        if not tasks:
            return 0, 0, ["No devices configured"]
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        total_count = len(results)
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"Device {list(self.devices.keys())[i]}: {str(result)}")
            elif result[0]:  # success
                success_count += 1
            else:
                errors.append(f"Device {list(self.devices.keys())[i]}: {result[1]}")
                
        return success_count, total_count, errors
        
    async def stop_all_recording(self) -> Tuple[int, int, List[str]]:
        """Stop recording on all devices"""
        tasks = []
        for device_id in self.devices.keys():
            tasks.append(self.stop_recording(device_id))
            
        if not tasks:
            return 0, 0, ["No devices configured"]
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        total_count = len(results)
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"Device {list(self.devices.keys())[i]}: {str(result)}")
            elif result[0]:  # success
                success_count += 1
            else:
                errors.append(f"Device {list(self.devices.keys())[i]}: {result[1]}")
                
        return success_count, total_count, errors
        
    async def start_all_intervals(self, interval_name: str = None) -> Tuple[int, int, List[str]]:
        """Start intervals on all devices"""
        tasks = []
        for device_id in self.devices.keys():
            tasks.append(self.start_interval(device_id, interval_name))
            
        if not tasks:
            return 0, 0, ["No devices configured"]
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        total_count = len(results)
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"Device {list(self.devices.keys())[i]}: {str(result)}")
            elif result[0]:  # success
                success_count += 1
            else:
                errors.append(f"Device {list(self.devices.keys())[i]}: {result[1]}")
                
        return success_count, total_count, errors
        
    async def end_all_intervals(self) -> Tuple[int, int, List[str]]:
        """End intervals on all devices"""
        tasks = []
        for device_id in self.devices.keys():
            tasks.append(self.end_interval(device_id))
            
        if not tasks:
            return 0, 0, ["No devices configured"]
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        total_count = len(results)
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"Device {list(self.devices.keys())[i]}: {str(result)}")
            elif result[0]:  # success
                success_count += 1
            else:
                errors.append(f"Device {list(self.devices.keys())[i]}: {result[1]}")
                
        return success_count, total_count, errors

# Global instance
lsl_controller = None

async def get_lsl_controller():
    """Get or create the global LSL controller instance"""
    global lsl_controller
    if lsl_controller is None:
        lsl_controller = LSLRemoteController()
        await lsl_controller.__aenter__()
    return lsl_controller

async def cleanup_lsl_controller():
    """Cleanup the global LSL controller instance"""
    global lsl_controller
    if lsl_controller is not None:
        await lsl_controller.__aexit__(None, None, None)
        lsl_controller = None 