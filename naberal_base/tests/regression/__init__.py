"""
Regression Tests

Lock-in 2/5: 회귀 테스트 (루프/라이프스팬 패턴)

Tests critical patterns to prevent regression of:
- Event loop is closed errors
- pytest-asyncio version conflicts
- ASGITransport lifespan issues
- Double dispose safety
"""
