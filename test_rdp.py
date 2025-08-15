#!/usr/bin/env python3
"""Test script to debug RDP connections"""

import subprocess
import sys

def test_connection(hostname, username, password):
    """Test a basic RDP connection"""
    
    # Basic command
    cmd = [
        "xfreerdp",
        f"/v:{hostname}",
        f"/u:{username}",
        f"/p:{password}",
        "/cert:ignore",
        "/size:1024x768"
    ]
    
    print(f"Testing connection to {hostname}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("Connection timed out after 10 seconds")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: ./test_rdp.py <hostname> <username> <password>")
        sys.exit(1)
    
    test_connection(sys.argv[1], sys.argv[2], sys.argv[3])