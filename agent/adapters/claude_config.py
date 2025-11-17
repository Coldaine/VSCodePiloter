from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def get_claude_desktop_config_path() -> Optional[Path]:
    """Get the path to Claude Desktop's config file."""
    if os.name == 'nt':  # Windows
        config_path = Path(os.environ.get('APPDATA', '')) / 'Claude' / 'claude_desktop_config.json'
    elif os.name == 'posix':  # macOS/Linux
        if 'darwin' in os.sys.platform:  # macOS
            config_path = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
        else:  # Linux
            config_path = Path.home() / '.config' / 'Claude' / 'claude_desktop_config.json'
    else:
        return None
    
    return config_path if config_path.exists() else None


def load_claude_mcp_servers() -> Dict[str, Dict[str, Any]]:
    """
    Load MCP server configurations from Claude Desktop's config file.
    
    Returns:
        Dictionary mapping server names to their configurations.
        Each config has 'command', 'args', and optionally 'env'.
    """
    config_path = get_claude_desktop_config_path()
    
    if not config_path:
        logger.info("Claude Desktop config not found")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        mcp_servers = config.get('mcpServers', {})
        logger.info(f"Loaded {len(mcp_servers)} MCP servers from Claude Desktop config")
        return mcp_servers
    
    except Exception as e:
        logger.warning(f"Failed to load Claude Desktop config: {e}")
        return {}


def get_windows_automation_server() -> Optional[Dict[str, Any]]:
    """
    Find a Windows automation MCP server from Claude Desktop's config.
    
    Looks for common Windows automation servers like:
    - mcp-control / MCPControl
    - windows-mcp / Windows-MCP
    - mcp-windows-desktop-automation
    
    Returns:
        Server configuration dict with 'command', 'args', 'env' or None if not found.
    """
    servers = load_claude_mcp_servers()
    
    # Check for known Windows automation servers
    automation_keywords = ['mcp-control', 'mcpcontrol', 'windows-mcp', 'windows', 'desktop-automation', 'automation']
    
    for name, config in servers.items():
        name_lower = name.lower()
        if any(keyword in name_lower for keyword in automation_keywords):
            logger.info(f"Found Windows automation server in Claude config: {name}")
            return {
                'name': name,
                'command': config.get('command', ''),
                'args': config.get('args', []),
                'env': config.get('env', {})
            }
    
    logger.info("No Windows automation server found in Claude Desktop config")
    return None


def get_default_mcp_server_config() -> Dict[str, Any]:
    """
    Get default MCP server configuration.
    
    Priority:
    1. Windows automation server from Claude Desktop config
    2. Fallback to mcp-control via npx
    
    Returns:
        Configuration dict with 'command', 'args', 'env'
    """
    # Try to use Claude Desktop's config
    claude_server = get_windows_automation_server()
    if claude_server:
        return claude_server
    
    # Fallback to Windows-MCP via npx
    logger.info("Using fallback MCP server: Windows-MCP via npx")
    return {
        'name': 'windows-mcp-fallback',
        'command': 'npx',
        'args': ['-y', '@curtsortouch/windows-mcp'],
        'env': {}
    }
