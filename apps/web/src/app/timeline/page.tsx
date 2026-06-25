"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { GitBranch } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/shared/empty-state";
import { ListSkeleton } from "@/components/shared/loading-skeletons";
import { useTimeline } from "@/hooks/use-queries";

export default function TimelinePage() {
  const { data, isLoading } = useTimeline();
  const entries = useMemo(() => data?.entries ?? [], [data?.entries]);

  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = entries.map((entry, i) => ({
      id: entry.id,
      position: { x: 250, y: i * 120 },
      data: {
        label: (
          <div className="rounded-lg border bg-card p-3 shadow-sm max-w-[220px]">
            <p className="font-medium text-sm">{entry.title}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {new Date(entry.occurred_at).toLocaleDateString()}
            </p>
            {entry.description && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{entry.description}</p>
            )}
          </div>
        ),
      },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
      style: { background: "transparent", border: "none", padding: 0 },
    }));

    const edges: Edge[] = entries.slice(0, -1).map((entry, i) => ({
      id: `e-${entry.id}`,
      source: entry.id,
      target: entries[i + 1].id,
      animated: true,
      style: { stroke: "var(--primary)" },
    }));

    return { nodes, edges };
  }, [entries]);

  return (
    <AppShell title="Timeline" description="Your study abroad journey visualized">
      {isLoading ? (
        <ListSkeleton />
      ) : entries.length === 0 ? (
        <EmptyState
          icon={GitBranch}
          title="No timeline events yet"
          description="Events appear as you upload documents, create applications, and interact with AI."
        />
      ) : (
        <div className="h-[calc(100vh-10rem)] rounded-xl border bg-card" role="img" aria-label="Application timeline flow">
          <ReactFlow nodes={nodes} edges={edges} fitView nodesDraggable={false} nodesConnectable={false}>
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      )}
    </AppShell>
  );
}
