/**
 * AI Manager Components
 *
 * 참조: 절대코어파일/AI_매니저_구현계획_V1.0.md
 *
 * 주요 컴포넌트:
 * - AIManagerLayout: 채팅/시각화 분할 레이아웃
 * - ChatPanel: ChatGPT 스타일 채팅 인터페이스
 * - VisualizationPanel: 결과 시각화 패널
 *
 * 훅:
 * - useTabController: 탭 통합 컨트롤러
 */

// Layout Components
export { AIManagerLayout } from "./AIManagerLayout";

// Panel Components
export { ChatPanel } from "./ChatPanel";
export { VisualizationPanel } from "./VisualizationPanel";

// Hooks
export { useTabController } from "./hooks/useTabController";
export type { TabController, TabType, CommandResult } from "./hooks/useTabController";
