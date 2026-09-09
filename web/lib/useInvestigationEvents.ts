"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { PipelineEvent } from "./types";


export function useInvestigationEvents(investigationId: string | null) {
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [refreshSignal, setRefreshSignal] = useState(0);
  const [connected, setConnected] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!investigationId) return;

    setEvents([]);
    const source = new EventSource(api.eventsUrl(investigationId));
    sourceRef.current = source;
    setConnected(true);

    source.onmessage = (msg) => {
      try {
        const event: PipelineEvent = JSON.parse(msg.data);
        setEvents((prev) => [...prev, event]);
        setRefreshSignal((n) => n + 1);
      } catch {
        
      }
    };

    source.onerror = () => {
      setConnected(false);
      source.close();
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [investigationId]);

  return { events, refreshSignal, connected };
}
