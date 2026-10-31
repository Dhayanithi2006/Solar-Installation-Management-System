#!/usr/bin/env python3
"""
SunPower Solutions — Odoo ERP MCP Health & Connectivity Audit
Verifies endpoint reachability, JSON-RPC handshake, Bearer token auth,
context initialization, and tool execution against the live Odoo MCP server.
"""

import sys
import json
import ssl
import urllib.request
import urllib.error

# Ensure UTF-8 output across Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

MCP_URL = "https://solar-installation-management-system.odoo.com/mcp"
AUTH_TOKEN = "e1f3185c8696cdb7ad0b5594c1b00a76e6b1dbe3_oak"

def run_healthcheck():
    print(f"\n{BOLD}SunPower Solutions — Live Odoo MCP Server Health Audit{RESET}")
    print(f"Target Endpoint: {MCP_URL}\n" + "=" * 75)

    ctx = ssl.create_default_context()
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Test 1: JSON-RPC initialize handshake
    print(f"1. Testing Protocol Handshake (initialize)...")
    init_payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'initialize',
        'params': {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'Antigravity-Audit', 'version': '1.0.0'}
        }
    }
    try:
        req = urllib.request.Request(MCP_URL, data=json.dumps(init_payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            srv_info = data.get('result', {}).get('serverInfo', {})
            proto = data.get('result', {}).get('protocolVersion', '')
            print(f"   [{GREEN}PASS{RESET}] Handshake Successful (Odoo {srv_info.get('version')}, Protocol: {proto})")
    except Exception as e:
        print(f"   [{RED}FAIL{RESET}] Handshake Failed: {e}")
        return 1

    # Test 2: Tool discovery (tools/list)
    print(f"2. Testing Tool Discovery (tools/list)...")
    tools_payload = {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}}
    try:
        req = urllib.request.Request(MCP_URL, data=json.dumps(tools_payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            tools = data.get('result', {}).get('tools', [])
            tool_names = [t['name'] for t in tools]
            print(f"   [{GREEN}PASS{RESET}] Discovered {len(tools)} tools: {', '.join(tool_names)}")
    except Exception as e:
        print(f"   [{RED}FAIL{RESET}] Tool Discovery Failed: {e}")
        return 1

    # Test 3: Context Retrieval (ai_tool_mcp_retrieve_initial_context)
    print(f"3. Testing Initial Context Retrieval...")
    context_payload = {
        'jsonrpc': '2.0',
        'id': 3,
        'method': 'tools/call',
        'params': {'name': 'ai_tool_mcp_retrieve_initial_context', 'arguments': {}}
    }
    try:
        req = urllib.request.Request(MCP_URL, data=json.dumps(context_payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            raw_text = data.get('result', {}).get('content', [{}])[0].get('text', '')
            print(f"   [{GREEN}PASS{RESET}] Context successfully loaded:")
            for line in raw_text.replace('\\n', '\n').split('\n'):
                if any(k in line for k in ['User info', 'Active company', 'Timezone']):
                    print(f"         -> {line.strip()}")
    except Exception as e:
        print(f"   [{RED}FAIL{RESET}] Context Retrieval Failed: {e}")
        return 1

    # Test 4: Live Search (ai_tool_search on res.partner)
    print(f"4. Testing Live Database Query (ai_tool_search -> res.partner)...")
    search_payload = {
        'jsonrpc': '2.0',
        'id': 4,
        'method': 'tools/call',
        'params': {
            'name': 'ai_tool_search',
            'arguments': {
                'model_name': 'res.partner',
                'domain': '[]',
                'fields': ['name', 'email'],
                'limit': 5
            }
        }
    }
    try:
        req = urllib.request.Request(MCP_URL, data=json.dumps(search_payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            txt = data.get('result', {}).get('content', [{}])[0].get('text', '')
            res_obj = json.loads(txt).get('response', {})
            total = res_obj.get('total_count', 0)
            records = res_obj.get('records', [])
            print(f"   [{GREEN}PASS{RESET}] Query executed successfully (Total Contacts: {total}):")
            for r in records[:3]:
                print(f"         -> [{r.get('id')}] {r.get('name')} <{r.get('email')}>")
    except Exception as e:
        print(f"   [{RED}FAIL{RESET}] Database Query Failed: {e}")
        return 1

    print("=" * 75)
    print(f"{GREEN}{BOLD}ALL 4 MCP HEALTH & CONNECTIVITY CHECKS PASSED WITH 100% SUCCESS!{RESET}\n")
    return 0

if __name__ == '__main__':
    sys.exit(run_healthcheck())

