"use client";

import { WebSocketProvider } from "@/context/websocket-context";
import { ReactNode } from "react";

interface WebSocketWrapperProps {
  children: ReactNode;
}

export function WebSocketWrapper({ children }: WebSocketWrapperProps) {
  return (
    <WebSocketProvider>
      {children}
    </WebSocketProvider>
  );
}