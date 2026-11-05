"""Compatibility entry point for the unchanged pre-fit-published residual package.

The pair was serialized by its build CLI, which recorded the dataclass as
__main__.ResidualRuntime. Bind exactly that canonical inference-only class in
this entry point; do not rewrite artifacts, refit heads or alter frozen sources.
"""
from ml.c1_history_residual_v1 import ResidualRuntime
from ml.run_c1_history_residual_v1 import main

if __name__ == '__main__':
    main()
