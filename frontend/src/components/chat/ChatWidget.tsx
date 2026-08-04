import { Minus, RotateCcw, Send, Sparkles, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "../../contexts/AuthContext";
import { sendChatMessage } from "../../lib/api";
import type { ChatTurn } from "../../lib/types";

function ChatMarkdown({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
        strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
        em: ({ children }) => <em className="italic">{children}</em>,
        ul: ({ children }) => <ul className="list-disc pl-4 mb-2 last:mb-0 space-y-0.5">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 last:mb-0 space-y-0.5">{children}</ol>,
        li: ({ children }) => <li className="leading-relaxed">{children}</li>,
        code: ({ children }) => (
          <code className="bg-gray-100 text-pink-600 rounded px-1 py-0.5 text-xs font-mono break-words">
            {children}
          </code>
        ),
        pre: ({ children }) => (
          <pre className="bg-gray-900 text-gray-100 rounded-lg p-2.5 mb-2 last:mb-0 text-xs overflow-x-auto">
            {children}
          </pre>
        ),
        a: ({ children, href }) => (
          <a href={href} target="_blank" rel="noreferrer" className="text-blue-600 underline">
            {children}
          </a>
        ),
        h1: ({ children }) => <h1 className="text-base font-semibold mb-1.5 mt-1 first:mt-0">{children}</h1>,
        h2: ({ children }) => <h2 className="text-sm font-semibold mb-1.5 mt-1 first:mt-0">{children}</h2>,
        h3: ({ children }) => <h3 className="text-sm font-semibold mb-1 mt-1 first:mt-0">{children}</h3>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-gray-300 pl-2 italic text-gray-600 mb-2 last:mb-0">
            {children}
          </blockquote>
        ),
        hr: () => <hr className="my-2 border-gray-200" />,
        table: ({ children }) => (
          <div className="overflow-x-auto mb-2 last:mb-0">
            <table className="text-xs border-collapse w-full">{children}</table>
          </div>
        ),
        th: ({ children }) => <th className="border border-gray-200 px-1.5 py-1 bg-gray-50 text-left">{children}</th>,
        td: ({ children }) => <td className="border border-gray-200 px-1.5 py-1">{children}</td>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

type PanelState = "collapsed" | "expanded" | "minimized";

function welcomeMessage(displayName: string | undefined): ChatTurn {
  const firstName = (displayName || "there").split(" ").slice(-1)[0];
  return {
    role: "assistant",
    content:
      `Hi ${firstName === "there" ? "" : "Dr. " + firstName} \u{1F44B}\n\n` +
      "I'm your AI Governance Assistant. I can help explain predictions, " +
      "investigate compliance, summarize trust metrics, and answer questions " +
      "about patients and AI decisions.",
  };
}

export default function ChatWidget() {
  const { user } = useAuth();
  const [panelState, setPanelState] = useState<PanelState>("collapsed");
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([welcomeMessage(user?.display_name)]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.display_name]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  if (!user) return null;

  const open = panelState === "expanded";

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const nextMessages: ChatTurn[] = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setSending(true);

    try {
      const historyForApi = nextMessages.filter((m, i) => !(i === 0 && m.role === "assistant"));
      const result = await sendChatMessage(text, historyForApi);
      setMessages((prev) => [...prev, { role: "assistant", content: result.reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong reaching the assistant. Please try again." },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleRefresh = () => {
    setMessages([welcomeMessage(user.display_name)]);
  };

  return (
    <>
      {panelState !== "expanded" && (
        <button
          onClick={() => setPanelState("expanded")}
          title="AI Assistant"
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full flex items-center justify-center
                     bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg
                     hover:shadow-[0_0_24px_rgba(99,102,241,0.55)] hover:scale-105
                     transition-all duration-200 ease-out z-50"
        >
          <Sparkles size={22} className="text-white" />
        </button>
      )}

      {open && (
        <div
          className="fixed bottom-6 right-6 flex flex-col bg-white shadow-2xl z-50
                     transition-all duration-[250ms] ease-out"
          style={{ width: 420, height: 720, maxHeight: "calc(100vh - 48px)", borderRadius: 18 }}
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Sparkles size={15} className="text-white" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <p className="font-semibold text-sm leading-tight">AI Governance Assistant</p>
                  <span className="badge-green" style={{ fontSize: 10, padding: "1px 6px" }}>
                    NEW
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1 text-gray-400">
              <button onClick={handleRefresh} title="Refresh conversation" className="p-1.5 rounded hover:bg-gray-100 hover:text-gray-700">
                <RotateCcw size={15} />
              </button>
              <button onClick={() => setPanelState("collapsed")} title="Minimize" className="p-1.5 rounded hover:bg-gray-100 hover:text-gray-700">
                <Minus size={15} />
              </button>
              <button onClick={() => setPanelState("collapsed")} title="Close" className="p-1.5 rounded hover:bg-gray-100 hover:text-gray-700">
                <X size={15} />
              </button>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4 bg-gray-50/50">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                {m.role === "assistant" && (
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles size={12} className="text-white" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm ${
                    m.role === "user"
                      ? "bg-blue-500 text-white rounded-br-sm whitespace-pre-wrap"
                      : "bg-white border border-gray-100 text-gray-800 rounded-bl-sm shadow-sm"
                  }`}
                >
                  {m.role === "assistant" ? <ChatMarkdown content={m.content} /> : m.content}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex gap-2 justify-start">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shrink-0">
                  <Sparkles size={12} className="text-white" />
                </div>
                <div className="bg-white border border-gray-100 rounded-2xl rounded-bl-sm px-3.5 py-2.5 shadow-sm">
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce" />
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-gray-100 p-3">
            <div className="flex items-end gap-2">
              <textarea
                className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none outline-none focus:border-blue-400"
                rows={1}
                placeholder="Ask about a patient, rule, or trend..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
              />
              <button
                onClick={handleSend}
                disabled={sending || !input.trim()}
                className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center
                           text-white disabled:opacity-40 shrink-0"
              >
                <Send size={15} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
