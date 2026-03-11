"""
Drawing Service - Generates manufacturing drawings (SVG/DXF) from estimate data
"""

import logging
import json
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from kis_estimator_core.core.ssot.errors import raise_error, ErrorCode

logger = logging.getLogger(__name__)

class DrawingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_drawing(self, estimate_id: str) -> Dict[str, Any]:
        """
        Generate drawing for the given estimate ID.
        
        Flow:
        1. Fetch estimate data (placements, enclosure) from DB
        2. Validate data
        3. Generate SVG/DXF (Simulated)
        4. Save evidence
        5. Return result
        """
        # 1. Fetch estimate data
        # We need to get the execution history or the plan to find the placements
        # For simplicity, let's assume we can get the 'BOM' stage output which contains 'estimate_data'
        # or 'Layout' stage output which contains 'placements'
        
        # Fetch Layout stage output
        result = await self.db.execute(
            text("""
                SELECT stage_output 
                FROM execution_history 
                WHERE estimate_id = :id AND stage_name = 'Layout' AND status = 'success'
                ORDER BY created_at DESC LIMIT 1
            """),
            {"id": estimate_id}
        )
        row = result.fetchone()
        
        if not row:
            raise_error(
                ErrorCode.E_NOT_FOUND,
                f"Layout data not found for estimate {estimate_id}",
                hint="Ensure the estimate has completed the Layout stage successfully"
            )
            
        layout_output = json.loads(row[0])
        placements = layout_output.get("placements", [])
        
        if not placements:
             raise_error(
                ErrorCode.E_VALIDATION,
                f"No placements found in Layout output for estimate {estimate_id}"
            )

        # 2. Generate SVG (Simulation)
        # In a real implementation, this would use a CAD library or SVG generator
        svg_content = self._generate_svg(placements)
        
        # 3. Save Evidence (Simulation)
        # We would save the SVG to a file and record it in the evidence table
        evidence_path = f"drawings/{estimate_id}.svg"
        
        return {
            "estimate_id": estimate_id,
            "drawing_type": "SVG",
            "path": evidence_path,
            "content_preview": svg_content[:100] + "...",
            "generated_at": "2025-12-01T12:00:00Z" # Placeholder
        }

    def _generate_svg(self, placements: list) -> str:
        """Simple SVG generator based on placements"""
        svg = '<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">\n'
        svg += '  <rect x="0" y="0" width="800" height="600" fill="#f0f0f0" stroke="black"/>\n'
        
        for p in placements:
            # Assuming placement has x, y, width, height
            # Adjust keys based on actual placement structure
            x = p.get("x", 0)
            y = p.get("y", 0)
            w = p.get("width_mm", 50)
            h = p.get("height_mm", 50)
            label = p.get("id", "Breaker")
            
            svg += f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" stroke="blue"/>\n'
            svg += f'  <text x="{x+5}" y="{y+20}" font-family="Arial" font-size="12">{label}</text>\n'
            
        svg += '</svg>'
        return svg
