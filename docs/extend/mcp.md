# MCP servers

Ana is an MCP ([Model Context Protocol](https://modelcontextprotocol.io))
client: it connects to MCP servers at backend startup and wraps each remote
tool as a normal Ana tool, so MCP tools behave exactly like built-in ones
from the agent's perspective — same permission gating, same secrets
redaction on output.

!!! note "stdio transport only"
    Servers are launched as local subprocesses over stdio. SSE/HTTP servers
    are not supported and raise on connect.

## Configuration

Global config lives in `~/.ana/mcp.json`; a project-level `.ana/mcp.json`
is also read:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@example/mcp-server"]
    }
  }
}
```

Manage from the CLI (or `/mcp` in chat):

```bash
ana mcp list      # configured servers
ana mcp add ...   # add a server to ~/.ana/mcp.json
ana mcp remove ...
ana mcp status    # connection status
```

!!! warning "Restart to connect"
    Servers are only connected at backend startup — restart the backend
    after adding or removing one.

## Trust model

MCP servers run as local subprocesses with your user's permissions, and
their tools are exposed to the agent exactly like built-in tools. Only
configure servers you trust — see
[Security](../reference/security.md#extensibility-trust-boundaries).

## Related

- [Tools](../features/tools.md) — how tool calls are gated
- [Plugins](plugins.md) — deeper (Python-level) extension
