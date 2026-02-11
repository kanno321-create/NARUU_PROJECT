"""플러그인 관리 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from naruu_api.deps import get_orchestrator, get_plugin_manager
from naruu_core.orchestrator import Orchestrator
from naruu_core.plugin_manager import PluginError, PluginManager

router = APIRouter(prefix="/plugins", tags=["plugins"])


class ExecuteRequest(BaseModel):
    """플러그인 명령 실행 요청."""

    command: str
    payload: dict[str, Any] = {}


class OrchestrateRequest(BaseModel):
    """자연어 오케스트레이션 요청."""

    message: str


class WorkflowStep(BaseModel):
    """워크플로우 단계."""

    plugin: str
    command: str
    payload: dict[str, Any] = {}


class WorkflowRequest(BaseModel):
    """워크플로우 실행 요청."""

    steps: list[WorkflowStep]


@router.get("")
async def list_plugins(
    pm: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """등록된 플러그인 목록."""
    plugins = pm.list_plugins()
    return {
        "count": len(plugins),
        "plugins": [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "capabilities": p.capabilities,
                "status": p.status.value,
            }
            for p in plugins
        ],
    }


@router.get("/{name}")
async def get_plugin(
    name: str,
    pm: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """플러그인 상세 정보."""
    plugin = pm.get(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"플러그인 '{name}'을(를) 찾을 수 없습니다")
    info = plugin.info()
    return {
        "name": info.name,
        "version": info.version,
        "description": info.description,
        "capabilities": info.capabilities,
        "status": info.status.value,
    }


@router.post("/{name}/execute")
async def execute_plugin(
    name: str,
    req: ExecuteRequest,
    pm: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """플러그인 명령 실행."""
    try:
        result = await pm.execute(name, req.command, req.payload)
        return {"success": True, "plugin": name, "command": req.command, "result": result}
    except PluginError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/orchestrate")
async def orchestrate(
    req: OrchestrateRequest,
    orch: Orchestrator = Depends(get_orchestrator),
) -> dict:
    """자연어 명령 → AI가 플러그인 라우팅."""
    result = await orch.route(req.message)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return {
        "success": result.success,
        "plugin": result.plugin,
        "command": result.command,
        "result": result.result,
    }


@router.post("/workflow")
async def run_workflow(
    req: WorkflowRequest,
    orch: Orchestrator = Depends(get_orchestrator),
) -> dict:
    """워크플로우(다단계) 실행."""
    steps = [
        {"plugin": s.plugin, "command": s.command, "payload": s.payload}
        for s in req.steps
    ]
    results = await orch.execute_workflow(steps)
    return {
        "total_steps": len(steps),
        "completed": sum(1 for r in results if r.success),
        "results": [
            {
                "plugin": r.plugin,
                "command": r.command,
                "success": r.success,
                "result": r.result,
                "error": r.error,
            }
            for r in results
        ],
    }
