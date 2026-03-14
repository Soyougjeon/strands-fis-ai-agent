import { useCallback, useEffect, useRef, useState } from "react";
import type { AgentEvent } from "../types";

interface UseWebSocketOptions {
  onEvent: (event: AgentEvent) => void;
}

export function useWebSocket({ onEvent }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const retriesRef = useRef(0);
  const maxRetries = 5;

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/ws/chat`);

    ws.onopen = () => {
      setConnected(true);
      retriesRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const parsed: AgentEvent = JSON.parse(event.data);
        onEvent(parsed);
      } catch {
        console.warn("Failed to parse WebSocket message:", event.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      if (retriesRef.current < maxRetries) {
        retriesRef.current += 1;
        setTimeout(connect, 3000);
      }
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [onEvent]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback(
    (sessionId: string | null, message: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ session_id: sessionId, message })
        );
      }
    },
    []
  );

  return { connected, sendMessage };
}
