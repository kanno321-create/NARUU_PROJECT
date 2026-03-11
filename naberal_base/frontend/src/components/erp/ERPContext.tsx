"use client";

import React, { createContext, useContext, ReactNode, useCallback, useState } from "react";

// 윈도우 관리 context - 전역 윈도우 관리
interface ERPContextType {
    openWindow: (type: string, title: string) => void;
    closeWindow: (id: string) => void;
}

const ERPContext = createContext<ERPContextType | null>(null);

interface ERPProviderProps {
    children: ReactNode;
    openWindow: (type: string, title: string) => void;
    closeWindow: (id: string) => void;
}

export function ERPProvider({ children, openWindow, closeWindow }: ERPProviderProps) {
    return (
        <ERPContext.Provider value={{ openWindow, closeWindow }}>
            {children}
        </ERPContext.Provider>
    );
}

export function useERP() {
    const context = useContext(ERPContext);
    if (!context) {
        throw new Error("useERP must be used within an ERPProvider");
    }
    return context;
}

export function useERPOptional() {
    return useContext(ERPContext);
}

// 개별 윈도우 context - 각 윈도우 내부에서 사용
interface WindowContextType {
    windowId: string;
    closeThisWindow: () => void;
}

const WindowContext = createContext<WindowContextType | null>(null);

interface WindowProviderProps {
    children: ReactNode;
    windowId: string;
    onClose: () => void;
}

export function WindowProvider({ children, windowId, onClose }: WindowProviderProps) {
    return (
        <WindowContext.Provider value={{ windowId, closeThisWindow: onClose }}>
            {children}
        </WindowContext.Provider>
    );
}

export function useWindowContext() {
    const context = useContext(WindowContext);
    if (!context) {
        throw new Error("useWindowContext must be used within a WindowProvider");
    }
    return context;
}

export function useWindowContextOptional() {
    return useContext(WindowContext);
}
