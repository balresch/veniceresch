"""Resource namespaces — one per logical endpoint group.

Resources are thin: each method takes kwargs matching the swagger request
body, forwards them to the client's ``_request_*`` helper, and returns a
parsed dict (or ``bytes`` for binary endpoints).
"""
