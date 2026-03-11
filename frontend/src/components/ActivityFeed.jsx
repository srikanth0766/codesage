import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { History, CheckCircle2, AlertCircle, FileCode2, Terminal as TerminalIcon } from 'lucide-react';

const BACKEND = 'http://localhost:8000';

export default function ActivityFeed() {
    const [activities, setActivities] = useState([]);

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchLogs = async () => {
        try {
            const res = await fetch(`${BACKEND}/logs`);
            if (res.ok) {
                const data = await res.json();
                const formattedLogs = data.logs
                    .filter(line => line.trim())
                    .map((line, ix) => {
                        let risk = 'low';
                        let icon = TerminalIcon;

                        // Basic heuristic mapping based on log text
                        if (line.toLowerCase().includes('error') || line.toLowerCase().includes('fail')) {
                            risk = 'high';
                            icon = AlertCircle;
                        } else if (line.toLowerCase().includes('success') || line.toLowerCase().includes('refactor')) {
                            risk = 'success';
                            icon = CheckCircle2;
                        } else if (line.toLowerCase().includes('analyz') || line.toLowerCase().includes('ast')) {
                            risk = 'low';
                            icon = FileCode2;
                        }

                        // Remove confusing timestamp brackets from raw text if present for cleaner UI
                        const cleanLine = line.replace(/^.*?\[.*?\]\s*/, '').trim();

                        return {
                            id: ix,
                            type: 'log',
                            desc: cleanLine.substring(0, 70) + (cleanLine.length > 70 ? '...' : ''),
                            time: '', // Real timestamps would require backend parsing
                            risk,
                            icon
                        };
                    })
                    .reverse(); // Newest first

                setActivities(formattedLogs);
            }
        } catch (e) {
            console.error("Failed to fetch logs:", e);
        }
    };

    const handleReset = async () => {
        try {
            const res = await fetch(`${BACKEND}/logs/reset`, { method: 'POST' });
            if (res.ok) {
                setActivities([]);
            }
        } catch (e) {
            console.error("Failed to reset logs:", e);
        }
    };

    return (
        <div className="glass-panel h-full flex flex-col border-t-white/10 border-l-white/10">
            <div className="p-6 border-b border-white/5 flex justify-between items-center">
                <div>
                    <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                        Action Log
                    </h2>
                    <div className="text-xs text-gray-400 font-mono tracking-widest mt-1 uppercase">Recent System Events</div>
                </div>
                <button 
                    onClick={handleReset}
                    className="p-2 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white group"
                    title="Clear Logs"
                >
                    <History size={18} className="group-hover:rotate-180 transition-transform duration-500" />
                </button>
            </div>

            <div className="flex-1 p-6 overflow-y-auto min-h-[400px]">
                {activities.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-500 font-mono text-sm opacity-50">
                        <TerminalIcon size={32} className="mb-4" />
                        Awaiting system telemetry...
                    </div>
                ) : (
                    <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-white/10 before:to-transparent">
                        {activities.map((item, i) => {
                            let colorClass = 'text-cyber-primary border-cyber-primary bg-cyber-primary/10';
                            if (item.risk === 'high') colorClass = 'text-cyber-danger border-cyber-danger bg-cyber-danger/10';
                            if (item.risk === 'success') colorClass = 'text-cyber-success border-cyber-success bg-cyber-success/10';

                            return (
                                <motion.div
                                    key={item.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.15 }}
                                    className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active"
                                >
                                    {/* Icon */}
                                    <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 bg-cyber-900 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm z-10 ${colorClass}`}>
                                        <item.icon size={16} />
                                    </div>

                                    {/* Content */}
                                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-white/5 bg-black/20 group-hover:bg-white/[0.02] transition-colors">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="font-bold text-white text-sm">{item.desc}</div>
                                        </div>
                                        <div className="text-xs font-mono text-gray-500 uppercase">{item.time}</div>
                                    </div>
                                </motion.div>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
