"""
Placement Visualizer - Evidence 생성 (SVG)
차단기 배치 결과를 시각화하여 증거 파일 생성
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from .breaker_placer import PanelSpec, PlacementResult


class PlacementVisualizer:
    """
    배치 결과 시각화 (SVG 생성)

    Evidence 경로: /spec_kit/evidence/{timestamp}/placement.svg
    """

    def __init__(self):
        self.scale = 0.5  # 1mm = 0.5px (축소)

    def generate_svg(
        self,
        placements: list[PlacementResult],
        panel: PanelSpec,
        output_path: Path,
    ) -> None:
        """
        SVG 파일 생성

        Args:
            placements: 배치 결과 목록
            panel: 패널 사양
            output_path: 출력 파일 경로
        """
        # SVG 캔버스 크기 (패널 크기 + 여백)
        margin = 50
        canvas_w = int(panel.width_mm * self.scale) + margin * 2
        canvas_h = int(panel.height_mm * self.scale) + margin * 2

        # SVG 루트 생성
        svg = ET.Element(
            "svg",
            {
                "xmlns": "http://www.w3.org/2000/svg",
                "width": str(canvas_w),
                "height": str(canvas_h),
                "viewBox": f"0 0 {canvas_w} {canvas_h}",
            },
        )

        # 배경 (흰색)
        ET.SubElement(
            svg,
            "rect",
            {
                "width": str(canvas_w),
                "height": str(canvas_h),
                "fill": "white",
            },
        )

        # 패널 외곽선
        panel_x = margin
        panel_y = margin
        panel_w = int(panel.width_mm * self.scale)
        panel_h = int(panel.height_mm * self.scale)

        ET.SubElement(
            svg,
            "rect",
            {
                "x": str(panel_x),
                "y": str(panel_y),
                "width": str(panel_w),
                "height": str(panel_h),
                "fill": "none",
                "stroke": "black",
                "stroke-width": "2",
            },
        )

        # 패널 정보 (상단 라벨)
        ET.SubElement(
            svg,
            "text",
            {
                "x": str(panel_x + 10),
                "y": str(panel_y - 10),
                "font-family": "Arial, sans-serif",
                "font-size": "14",
                "fill": "black",
            },
        ).text = f"Panel: {panel.width_mm}×{panel.height_mm}×{panel.depth_mm}mm"

        # 차단기 배치 그리기
        phase_colors = {"L1": "#FF6B6B", "L2": "#4ECDC4", "L3": "#95E1D3"}

        for p in placements:
            x_px = margin + int(p.position["x"] * self.scale)
            y_px = margin + int(p.position["y"] * self.scale)

            # 차단기 크기 (기본값: 폴수에 따라)
            if p.poles == 2:
                w_px = int(50 * self.scale)  # 2P: 50mm
            elif p.poles == 3:
                w_px = int(75 * self.scale)  # 3P: 75mm
            elif p.poles == 4:
                w_px = int(100 * self.scale)  # 4P: 100mm
            else:
                w_px = int(50 * self.scale)

            h_px = int(130 * self.scale)  # 높이: 130mm (50AF 기본)

            # 차단기 색상 (phase 기반)
            color = phase_colors.get(p.phase, "#CCCCCC")

            # 차단기 사각형
            ET.SubElement(
                svg,
                "rect",
                {
                    "x": str(x_px - w_px // 2),
                    "y": str(y_px),
                    "width": str(w_px),
                    "height": str(h_px),
                    "fill": color,
                    "stroke": "black",
                    "stroke-width": "1",
                    "opacity": "0.7",
                },
            )

            # 차단기 ID 라벨
            ET.SubElement(
                svg,
                "text",
                {
                    "x": str(x_px),
                    "y": str(y_px + h_px // 2),
                    "font-family": "Arial, sans-serif",
                    "font-size": "10",
                    "fill": "black",
                    "text-anchor": "middle",
                },
            ).text = f"{p.breaker_id}"

            # Phase 라벨
            ET.SubElement(
                svg,
                "text",
                {
                    "x": str(x_px),
                    "y": str(y_px + h_px // 2 + 15),
                    "font-family": "Arial, sans-serif",
                    "font-size": "8",
                    "fill": "black",
                    "text-anchor": "middle",
                },
            ).text = f"{p.phase} {p.current_a}A"

        # 범례 (우측 상단)
        legend_x = panel_x + panel_w - 120
        legend_y = panel_y + 20

        ET.SubElement(
            svg,
            "text",
            {
                "x": str(legend_x),
                "y": str(legend_y),
                "font-family": "Arial, sans-serif",
                "font-size": "12",
                "font-weight": "bold",
                "fill": "black",
            },
        ).text = "Phase Legend:"

        for idx, (phase, color) in enumerate(phase_colors.items()):
            y_offset = legend_y + 20 + idx * 20

            # 색상 박스
            ET.SubElement(
                svg,
                "rect",
                {
                    "x": str(legend_x),
                    "y": str(y_offset - 10),
                    "width": "15",
                    "height": "15",
                    "fill": color,
                    "stroke": "black",
                    "stroke-width": "1",
                },
            )

            # 라벨
            ET.SubElement(
                svg,
                "text",
                {
                    "x": str(legend_x + 20),
                    "y": str(y_offset),
                    "font-family": "Arial, sans-serif",
                    "font-size": "10",
                    "fill": "black",
                },
            ).text = phase

        # XML 포맷팅 및 저장
        xml_str = minidom.parseString(ET.tostring(svg)).toprettyxml(indent="  ")

        # XML 선언 제거 (SVG에는 불필요)
        xml_lines = xml_str.split("\n")
        svg_content = "\n".join(
            [line for line in xml_lines if not line.startswith("<?xml")]
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(svg_content, encoding="utf-8")
