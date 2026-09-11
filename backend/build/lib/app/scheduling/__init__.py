"""Pure scheduling algorithms (no DB/infra imports).

- ``graph``: dependency DAG construction, cycle detection, topological order.
- ``critical_path``: Critical Path Method (forward/backward pass, slack, CP).

Everything here operates on plain identifiers/dataclasses so it is exhaustively
unit-testable without a database.
"""
