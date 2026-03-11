import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Terminal } from 'lucide-react';

const BACKEND = 'http://localhost:8000';

export default function TerminalPage() {
    const [logs, setLogs] = useState([]);
    const [isPolling, setIsPolling] = useState(true);
    const [inputValue, setInputValue] = useState('');
    const [localOutputs, setLocalOutputs] = useState([]);
    const scrollRef = useRef(null);

    useEffect(() => {
        let interval;
        const fetchLogs = async () => {
            try {
                const res = await fetch(`${BACKEND}/logs`);
                if (res.ok) {
                    const data = await res.json();
                    setLogs(data.logs);
                }
            } catch (e) {
                console.error("Failed to fetch logs", e);
            }
        };

        if (isPolling) {
            fetchLogs();
            interval = setInterval(fetchLogs, 2000);
        }

        return () => clearInterval(interval);
    }, [isPolling]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, localOutputs]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            const cmd = inputValue.trim();
            if (!cmd) return;

            const newOutput = [...localOutputs, { type: 'cmd', text: `admin@system:~$ ${cmd}` }];

            if (cmd === 'clear') {
                setLocalOutputs([]);
            } else if (cmd === 'help') {
                newOutput.push({ type: 'sys', text: 'Available commands: help, clear, ping, status' });
                setLocalOutputs(newOutput);
            } else if (cmd === 'ping') {
                newOutput.push({ type: 'sys', text: 'pong' });
                setLocalOutputs(newOutput);
            } else if (cmd === 'status') {
                newOutput.push({ type: 'sys', text: 'CodeSage Core: ONLINE\\nRisk Engine: SYNCED\\nAgent: READY' });
                setLocalOutputs(newOutput);
            } else {
                newOutput.push({ type: 'sys', text: `bash: ${cmd}: command not found` });
                setLocalOutputs(newOutput);
            }

            setInputValue('');
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="flex flex-col gap-8 pb-24 h-full"
        >
            <div className="flex items-center gap-4 border-b border-white/5 pb-6">
                <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-gray-300">
                    <Terminal size={32} />
                </div>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white drop-shadow-md">
                        Server Terminal
                    </h1>
                    <p className="text-sm text-gray-400 font-mono mt-1">
                        Direct console access to the backend management system.
                    </p>
                </div>
            </div>

            <div className="flex-1 min-h-[500px] glass-panel p-6 border-t-white/10 border-l-white/10 font-mono text-sm text-gray-300 relative overflow-hidden flex flex-col">
                <div className="flex-none h-8 bg-black/40 border-b border-white/5 flex items-center px-4 gap-2 justify-between">
                    <div className="flex gap-2">
                        <div className="w-2.5 h-2.5 rounded-full bg-cyber-danger"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-cyber-warning"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-cyber-success"></div>
                    </div>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsPolling(!isPolling)}
                            className={`text-xs ${isPolling ? 'text-cyber-success' : 'text-gray-500'} hover:text-white transition-colors`}
                        >
                            {isPolling ? '● Live' : '○ Paused'}
                        </button>
                        <span className="text-xs text-gray-500">root@codesage-core:~</span>
                    </div>
                </div>

                <div
                    ref={scrollRef}
                    className="flex-1 pt-4 overflow-y-auto pb-4 px-2 space-y-1"
                >
                    <div className="text-cyber-primary mb-4 opacity-70">CodeSage Interactive Shell v1.0.0 — Streaming /var/log/codesage/backend.log</div>

                    {logs.length === 0 ? (
                        <div className="opacity-50 italic text-gray-500">Waiting for log stream...</div>
                    ) : (
                        logs.map((line, idx) => {
                            let colorClass = "text-gray-400";
                            if (line.includes("ERROR") || line.includes("Exception") || line.includes("WARNING")) colorClass = "text-red-400";
                            else if (line.includes("INFO")) colorClass = "text-blue-300";
                            else if (line.includes("200 OK")) colorClass = "text-cyber-success";

                            return (
                                <div key={idx} className={`${colorClass} whitespace-pre-wrap break-all`}>
                                    {line.trim()}
                                </div>
                            );
                        })
                    )}

                    {localOutputs.map((item, idx) => (
                        <div key={`loc-${idx}`} className={item.type === 'cmd' ? "text-cyber-success" : "text-gray-400 whitespace-pre-wrap"}>
                            {item.text}
                        </div>
                    ))}

                    <div className="mt-4 flex gap-2 items-center">
                        <span className="text-cyber-success whitespace-nowrap">admin@system:~$</span>
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="bg-transparent border-none outline-none text-gray-300 w-full font-mono flex-1 caret-white"
                            autoFocus
                            spellCheck="false"
                            autoComplete="off"
                        />
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
