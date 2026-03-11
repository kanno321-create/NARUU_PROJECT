"use client";

import React, { useState, useRef, useEffect, ReactNode } from "react";
import { createPortal } from "react-dom";

interface DraggableModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  width?: string;
  initialPosition?: { x: number; y: number };
  /** 배경 오버레이 표시 여부 (기본: true) */
  showOverlay?: boolean;
  /** 모달 최소화/포커스를 위한 z-index (기본: 50) */
  zIndex?: number;
}

export function DraggableModal({
  isOpen,
  onClose,
  title,
  children,
  width = "400px",
  initialPosition,
  showOverlay = true,
  zIndex = 50,
}: DraggableModalProps) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [mounted, setMounted] = useState(false);
  const dragOffset = useRef({ x: 0, y: 0 });
  const modalRef = useRef<HTMLDivElement>(null);

  // 클라이언트 사이드에서만 마운트
  useEffect(() => {
    setMounted(true);
  }, []);

  // 모달이 열릴 때 중앙에 위치
  useEffect(() => {
    if (isOpen && modalRef.current) {
      if (initialPosition) {
        setPosition(initialPosition);
      } else {
        const modalWidth = modalRef.current.offsetWidth;
        const modalHeight = modalRef.current.offsetHeight;
        setPosition({
          x: (window.innerWidth - modalWidth) / 2,
          y: (window.innerHeight - modalHeight) / 2,
        });
      }
    }
  }, [isOpen, initialPosition]);

  // 드래그 핸들러
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        setPosition({
          x: e.clientX - dragOffset.current.x,
          y: e.clientY - dragOffset.current.y,
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (modalRef.current) {
      dragOffset.current = {
        x: e.clientX - position.x,
        y: e.clientY - position.y,
      };
      setIsDragging(true);
    }
  };

  if (!isOpen) return null;

  // 모달 컨텐츠 - fixed position으로 화면 어디든 자유롭게 이동 가능
  const modalContent = (
    <div
      ref={modalRef}
      className="fixed rounded-lg bg-white shadow-xl border border-gray-300"
      style={{
        left: position.x,
        top: position.y,
        width,
        zIndex: zIndex,
      }}
    >
        {/* 드래그 가능한 헤더 */}
        <div
          className="flex cursor-move items-center justify-between border-b px-4 py-3 select-none"
          onMouseDown={handleMouseDown}
        >
          <h3 className="font-semibold">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            onMouseDown={(e) => e.stopPropagation()}
          >
            ✕
          </button>
        </div>
      {/* 모달 내용 */}
      {children}
    </div>
  );

  // Portal을 사용하여 document.body에 직접 렌더링 (부모 컨테이너 제한 탈출)
  const portalContent = showOverlay ? (
    <div className="fixed inset-0 bg-black/50" style={{ zIndex: zIndex - 1 }}>
      {modalContent}
    </div>
  ) : (
    // 오버레이 없이 모달만 - 메인창 밖으로 자유롭게 이동 가능
    modalContent
  );

  // SSR 대응: 클라이언트에서만 렌더링
  if (!mounted || typeof document === "undefined") return null;

  return createPortal(portalContent, document.body);
}
