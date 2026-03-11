"""
Verb Engine - BaseVerb and Factory

I-3.2: ExecutionCtx 기반 Verb 규약 통일
I-3.3: REGISTRY lazy initialization (순환 import 방지)
"""

from .base import BaseVerb
from .factory import from_spec, from_spec_list, get_registry, register_verb

# I-3.2: VerbFactory는 함수로 제공 (클래스 아님)
# I-3.3: get_registry 추가 (REGISTRY 접근)
__all__ = ["BaseVerb", "from_spec", "from_spec_list", "register_verb", "get_registry"]
