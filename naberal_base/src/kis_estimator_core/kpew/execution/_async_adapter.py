"""
Async/Sync Adapter for Stage Runner
Safe invocation of sync or async callable in async context

Purpose:
- Prevents "asyncio.run() cannot be called from a running event loop" errors
- Provides universal interface for mixed async/sync stage functions
- Enables pytest-asyncio compatibility

Usage:
    from ._async_adapter import invoke_maybe_async

    async def run_stage(stage_func, plan, context):
        # Works for both async and sync stage functions
        return await invoke_maybe_async(stage_func, plan, context)
"""

import inspect
from collections.abc import Callable
from typing import Any


async def invoke_maybe_async(fn: Callable, *args, **kwargs) -> Any:
    """
    Safely invoke sync or async callable in async context.

    Rules:
      1. If fn is coroutine function (async def) → await fn(...)
      2. If fn is sync function → call directly, check if result is awaitable
      3. If result is accidentally awaitable → await it safely

    This prevents "asyncio.run() from a running event loop" errors.

    Args:
        fn: Callable (sync or async function)
        *args: Positional arguments to pass to fn
        **kwargs: Keyword arguments to pass to fn

    Returns:
        Result from fn (awaited if necessary)

    Raises:
        Any exception raised by fn

    Examples:
        >>> # Async stage function
        >>> async def async_stage(plan, ctx):
        ...     return {"result": "async"}
        >>> result = await invoke_maybe_async(async_stage, plan, ctx)

        >>> # Sync stage function
        >>> def sync_stage(plan, ctx):
        ...     return {"result": "sync"}
        >>> result = await invoke_maybe_async(sync_stage, plan, ctx)
    """
    # Check if function is async (coroutine function)
    if inspect.iscoroutinefunction(fn):
        # Directly await async function
        return await fn(*args, **kwargs)

    # Sync function - call directly
    result = fn(*args, **kwargs)

    # If result is accidentally awaitable (e.g., coroutine object returned)
    # await it to prevent "coroutine was never awaited" warning
    if inspect.isawaitable(result):
        return await result

    # Otherwise return sync result as-is
    return result
