#!/usr/bin/env python3
"""
Test script for Anthropic API Proxy

Tests the complete flow:
1. Authentication
2. Message creation
3. Tool calls
4. Streaming
5. MCP callbacks
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8084"  # Change to https://api.unicorncommander.ai in production
API_KEY = "test-api-key"  # Replace with real API key

def test_health_check():
    """Test health endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_list_models():
    """Test models list endpoint"""
    print("\n=== Testing List Models ===")
    response = requests.get(
        f"{BASE_URL}/v1/models",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_simple_message():
    """Test simple message without tools"""
    print("\n=== Testing Simple Message ===")

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {
                "role": "user",
                "content": "Write a Python function to calculate fibonacci numbers"
            }
        ],
        "max_tokens": 1024,
        "system": "You are a helpful coding assistant"
    }

    response = requests.post(
        f"{BASE_URL}/v1/messages",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Message ID: {data['id']}")
        print(f"Model: {data['model']}")
        print(f"Stop Reason: {data['stop_reason']}")
        print(f"Usage: {data['usage']}")
        print(f"\nContent:")
        for block in data['content']:
            if block['type'] == 'text':
                print(block['text'][:200] + "..." if len(block['text']) > 200 else block['text'])
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_message_with_tools():
    """Test message with tool calls"""
    print("\n=== Testing Message with Tools ===")

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {
                "role": "user",
                "content": "Read the file /etc/hostname and tell me what it contains"
            }
        ],
        "max_tokens": 1024,
        "system": "You are a helpful assistant with file system access",
        "tools": [
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]
    }

    response = requests.post(
        f"{BASE_URL}/v1/messages",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Message ID: {data['id']}")
        print(f"Stop Reason: {data['stop_reason']}")

        print(f"\nContent:")
        for block in data['content']:
            if block['type'] == 'text':
                print(f"Text: {block['text']}")
            elif block['type'] == 'tool_use':
                print(f"Tool Call: {block['name']}")
                print(f"Input: {json.dumps(block['input'], indent=2)}")

        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_streaming():
    """Test streaming endpoint"""
    print("\n=== Testing Streaming ===")

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {
                "role": "user",
                "content": "Count from 1 to 5 slowly"
            }
        ],
        "max_tokens": 1024,
        "stream": True
    }

    response = requests.post(
        f"{BASE_URL}/v1/messages/stream",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        stream=True
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Streaming response:")
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = line_str[6:]
                    if data != '[DONE]':
                        try:
                            event = json.loads(data)
                            print(f"Event: {event.get('type', 'unknown')}")
                            if event.get('type') == 'content_block_delta':
                                delta = event.get('delta', {})
                                if delta.get('type') == 'text_delta':
                                    print(f"Text: {delta.get('text', '')}", end='', flush=True)
                        except json.JSONDecodeError:
                            print(f"Invalid JSON: {data}")
        print("\n")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_mcp_status():
    """Test MCP callback status"""
    print("\n=== Testing MCP Status ===")

    response = requests.get(f"{BASE_URL}/api/mcp/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_mcp_registration():
    """Test MCP server registration"""
    print("\n=== Testing MCP Registration ===")

    payload = {
        "user_id": "test-user-123",
        "server_id": "local-tools",
        "tools": ["read_file", "write_file", "bash", "glob", "grep"],
        "method": "websocket"
    }

    response = requests.post(
        f"{BASE_URL}/api/mcp/register",
        headers={"Content-Type": "application/json"},
        json=payload
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Anthropic API Proxy Test Suite")
    print("=" * 60)

    tests = [
        ("Health Check", test_health_check),
        ("List Models", test_list_models),
        ("Simple Message", test_simple_message),
        ("Message with Tools", test_message_with_tools),
        ("Streaming", test_streaming),
        ("MCP Status", test_mcp_status),
        ("MCP Registration", test_mcp_registration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\nTest failed with exception: {e}")
            results.append((test_name, False))
        time.sleep(1)  # Small delay between tests

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
