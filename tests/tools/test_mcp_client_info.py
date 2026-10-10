"""Hermes declares its own ``clientInfo`` to MCP servers.

Without an explicit ``client_info`` the SDK falls back to ``Implementation(name="mcp")``, so
servers that derive an actor or policy from the client name saw a generic ``mcp`` client.
"""

import asyncio

import anyio

from hermes_cli import __version__
from tools import mcp_tool
from tools.mcp_tool import MCPServerTask


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def test_session_kwargs_declare_hermes():
    mcp_tool._ensure_mcp_sdk()
    info = MCPServerTask("ci_srv")._session_kwargs()["client_info"]
    assert (info.name, info.version) == ("hermes", __version__)


def test_client_session_carries_the_declared_identity():
    mcp_tool._ensure_mcp_sdk()
    send, recv = anyio.create_memory_object_stream(1)
    session = mcp_tool.ClientSession(recv, send, **MCPServerTask("ci_srv")._session_kwargs())
    assert session._client_info.name == "hermes"


def test_manual_handshake_falls_back_to_hermes():
    import mcp.types as types

    class _Session:
        sent = None

        async def send_request(self, request, result_type):
            self.sent = request
            return types.InitializeResult(
                protocolVersion="2026-07-28", capabilities=types.ServerCapabilities(),
                serverInfo=types.Implementation(name="srv", version="1"))

        def adopt(self, result):
            pass

        async def send_notification(self, notification):
            pass

    s = _Session()
    _run(MCPServerTask("ci_srv")._complete_handshake_at_offered_version(s))
    assert s.sent.params.client_info.name == "hermes"
