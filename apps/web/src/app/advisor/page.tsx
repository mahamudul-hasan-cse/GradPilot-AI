"use client";

import { useState } from "react";
import { Bot, Loader2, Send } from "lucide-react";
import { useSession } from "next-auth/react";
import { motion, AnimatePresence } from "framer-motion";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Message = { role: "user" | "assistant"; content: string };

const SUGGESTIONS = [
  "What universities match my profile?",
  "How can I improve my SOP?",
  "What scholarships am I eligible for?",
  "Explain the visa process for Canada",
];

export default function AdvisorPage() {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hi! I'm your GradPilot AI advisor. Ask me anything about studying abroad." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>();

  async function sendMessage(text: string) {
    if (!text.trim() || !session?.accessToken) return;
    const userMsg: Message = { role: "user", content: text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.ai.chat(session.accessToken, text, sessionId);
      setSessionId(res.session_id);
      setMessages((m) => [...m, { role: "assistant", content: res.response }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Sorry, I couldn't process that. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell title="AI Advisor" description="Personalized study abroad guidance">
      <div className="flex h-[calc(100vh-8rem)] flex-col">
        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-4 pb-4" role="log" aria-live="polite" aria-label="Chat messages">
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn("flex gap-3", msg.role === "user" && "flex-row-reverse")}
                >
                  {msg.role === "assistant" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      <Bot className="h-4 w-4" aria-hidden />
                    </div>
                  )}
                  <Card className={cn("max-w-[80%]", msg.role === "user" && "bg-primary text-primary-foreground")}>
                    <CardContent className="p-3 text-sm">{msg.content}</CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
            {loading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                Thinking...
              </div>
            )}
          </div>
        </ScrollArea>

        {messages.length <= 1 && (
          <div className="mb-4 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <Button key={s} variant="outline" size="sm" onClick={() => sendMessage(s)}>
                {s}
              </Button>
            ))}
          </div>
        )}

        <form
          className="flex gap-2 border-t pt-4"
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
        >
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your AI advisor..."
            rows={2}
            className="resize-none"
            aria-label="Message input"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage(input);
              }
            }}
          />
          <Button type="submit" size="icon" className="h-auto shrink-0" disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" aria-hidden />
            <span className="sr-only">Send message</span>
          </Button>
        </form>
      </div>
    </AppShell>
  );
}
