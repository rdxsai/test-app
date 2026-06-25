"""
Student learner-state package.

Direct PostgreSQL access (own connection pool, ``student_mcp`` schema) for
student profiles, mastery tracking, session state, and misconception logging
used by the guided Socratic tutor. Accessed at runtime via
``question_app.services.student_service.StudentService``. The historical MCP
server / stdio-client layer has been removed; the ``mcp`` name is retained only
for the schema and package path.
"""
