"""
Student MCP Server package.

A Model Context Protocol server that manages student profiles, mastery tracking,
session state, and misconception logging for the Socratic tutor chatbot.

Runs as a subprocess over stdio. The FastAPI backend connects as a client
using the same MCP client library used for wcag-guidelines-mcp.
"""
