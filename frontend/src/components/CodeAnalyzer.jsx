import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Code2, Play, GitMerge, AlertCircle, ShieldAlert, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import clsx from 'clsx';

const BACKEND = 'http://localhost:8000';

export default function CodeAnalyzer() {
    const [code, setCode] = useState('');
    const [smells, setSmells] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [hasRun, setHasRun] = useState(false);
    const [prevSmellCount, setPrevSmellCount] = useState(null);
    const [syncMessage, setSyncMessage] = useState('');
    const [isRefactoring, setIsRefactoring] = useState(false);
    const [refactorError, setRefactorError] = useState('');
    const [optimizedCode, setOptimizedCode] = useState('');
    const [activeTab, setActiveTab] = useState('smells'); // 'smells' | 'optimized'
    const [showOptimized, setShowOptimized] = useState(false);

    const loadExample = () => {
        setCode(`class OrderProcessor:
    def __init__(self):
        self.orders = []
        self.db = None
        
    def process_all_orders_in_system(self, user_id, auth_token, start_date, end_date, include_archived, notify_user):
        if not auth_token:
            if not user_id:
                if not start_date:
                    print("Invalid params")
                    return
                    
        for order in self.orders:
            if order.status == "pending":
                if order.total > 1000:
                    if order.user.is_vip:
                        print("Processing VIP large order")
                        
        # Simulating a very long method with filler
${Array(35).fill('        print("Processing...")').join('\\n')}
        return True`);
        setSmells([]);
        setHasRun(false);
    };

    const analyzeCode = async () => {
        if (!code.trim()) return;
        setLoading(true);
        setError('');
        setSyncMessage('');
        setOptimizedCode('');
        setShowOptimized(false);
        setActiveTab('smells');
        setHasRun(true);
        try {
            const res = await fetch(`${BACKEND}/analyze-smells`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language: 'python' })
            });
            if (!res.ok) throw new Error(`Analysis rejected: ${res.statusText}`);
            const data = await res.json();
            const currentSmellCount = data.smells?.length || 0;
            const detectedSmells = data.smells || [];
            setSmells(detectedSmells);

            // Auto-log deltas to the latest sprint if this isn't the first run
            if (prevSmellCount !== null) {
                let smells_delta = 0;
                let refactor_delta = 0;

                if (currentSmellCount > prevSmellCount) {
                    smells_delta = currentSmellCount - prevSmellCount;
                } else if (prevSmellCount > currentSmellCount) {
                    refactor_delta = prevSmellCount - currentSmellCount;
                }

                if (smells_delta > 0 || refactor_delta > 0) {
                    try {
                        const syncRes = await fetch(`${BACKEND}/update-latest-sprint`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ smells_delta, refactor_delta })
                        });
                        const syncData = await syncRes.json();
                        if (syncData.status === "updated") {
                            setSyncMessage(`Logged to active sprint: ${smells_delta > 0 ? `+${smells_delta} smells` : ''} ${refactor_delta > 0 ? `+${refactor_delta} refactors` : ''}`);
                        }
                    } catch (syncErr) {
                        console.error("Failed to sync with sprint:", syncErr);
                    }
                }
            }

            setPrevSmellCount(currentSmellCount);

            // Auto-fetch optimized code if smells were found
            if (detectedSmells.length > 0) {
                const topSmell = detectedSmells.reduce((prev, current) => (prev.confidence > current.confidence) ? prev : current);
                try {
                    setIsRefactoring(true);
                    const refactorRes = await fetch(`${BACKEND}/refactor`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            code,
                            language: 'python',
                            smell: topSmell.smell,
                            confidence: topSmell.confidence
                        })
                    });
                    if (refactorRes.ok) {
                        const refactorData = await refactorRes.json();
                        if (refactorData.success && refactorData.refactored_code) {
                            setOptimizedCode(refactorData.refactored_code);
                            setShowOptimized(true);
                        }
                    }
                } catch (refactorErr) {
                    console.error('Auto-refactor failed:', refactorErr);
                } finally {
                    setIsRefactoring(false);
                }
            }
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRefactor = async () => {
        if (smells.length === 0 || !code.trim()) return;

        // Find highest confidence smell to refactor first
        const topSmell = smells.reduce((prev, current) => (prev.confidence > current.confidence) ? prev : current);

        setIsRefactoring(true);
        setError('');
        setRefactorError('');
        setSyncMessage('');

        try {
            const res = await fetch(`${BACKEND}/refactor`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code,
                    language: 'python',
                    smell: topSmell.smell,
                    confidence: topSmell.confidence
                })
            });

            if (!res.ok) throw new Error(`Refactor failed: ${res.statusText}`);

            const data = await res.json();

            if (data.success && data.refactored_code) {
                setCode(data.refactored_code);
                setSyncMessage('✓ Code optimized by Mistral. Re-scanning recommended.');
                setRefactorError('');
            } else {
                setRefactorError(data.notes || data.error || 'Failed to generate valid refactored code.');
            }
        } catch (e) {
            setError(e.message);
        } finally {
            setIsRefactoring(false);
        }
    };

    return (
        <div className="glass-panel w-full border-t-white/10 border-l-white/10 overflow-hidden relative">
            {/* Background decoration */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-cyber-secondary/10 blur-[100px] rounded-full pointer-events-none -translate-y-1/2 translate-x-1/2" />

            <div className="p-6 border-b border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
                <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-cyber-primary/10 border border-cyber-primary/20 text-cyber-primary shadow-neon-primary">
                        <Code2 size={24} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-white tracking-wide">CodeSage Neural Auditor</h2>
                        <div className="text-xs text-cyber-primary/60 font-mono tracking-widest mt-0.5 uppercase">Paste Source For Analysis</div>
                    </div>
                </div>
                <button
                    onClick={analyzeCode}
                    disabled={loading || !code.trim()}
                    className="cyber-button flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <div className="w-5 h-5 border-2 border-cyber-primary border-t-transparent rounded-full animate-spin" />
                    ) : (
                        <>
                            <Play size={16} className="group-hover:text-white transition-colors" />
                            <span className="font-mono tracking-widest uppercase text-xs">Execute Scan</span>
                        </>
                    )}
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[400px] relative z-10">

                {/* Editor Pane */}
                <div className="border-b lg:border-b-0 lg:border-r border-white/5 relative group">
                    <div className="absolute top-3 left-4 text-[10px] font-mono text-gray-500 uppercase tracking-widest pointer-events-none z-20 flex gap-4">
                        <span>input.py</span>
                        <span className="text-cyber-primary/40 group-focus-within:text-cyber-primary transition-colors">Editing</span>
                    </div>
                    <button
                        onClick={loadExample}
                        className="absolute top-2 right-4 text-[10px] font-mono bg-white/5 hover:bg-white/10 text-gray-400 px-2 py-1 rounded transition-colors z-20"
                    >
                        LOAD EXAMPLE
                    </button>
                    {/* Minimal line numbers illusion */}
                    <div className="absolute left-0 top-0 bottom-0 w-12 bg-black/20 border-r border-white/5 flex flex-col items-end pt-12 pr-2 font-mono text-[10px] text-gray-600 space-y-1 select-none pointer-events-none">
                        {[...Array(15)].map((_, i) => <div key={i}>{i + 1}</div>)}
                    </div>
                    <textarea
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        className="w-full h-full min-h-[400px] bg-transparent text-gray-300 font-mono text-sm p-4 pt-12 pl-16 resize-none focus:outline-none focus:ring-1 focus:ring-inset focus:ring-cyber-primary/50"
                        spellCheck="false"
                        placeholder="def god_class_example():&#10;    # Write or paste Python code here&#10;    pass"
                    />
                </div>

                {/* Results Pane */}
                <div className="bg-black/40 p-6 flex flex-col relative overflow-hidden">
                    <div className="absolute inset-0 bg-glass-glow opacity-50 pointer-events-none" />

                    <div className="flex items-center justify-between mb-6 z-10">
                        <h3 className="text-xs font-mono text-gray-500 uppercase tracking-widest flex items-center gap-2">
                            <GitMerge size={14} /> Telemetry Output
                        </h3>
                        {syncMessage && (
                            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="text-[10px] font-mono bg-cyber-primary/10 text-cyber-primary px-3 py-1 rounded-full border border-cyber-primary/20">
                                {syncMessage}
                            </motion.div>
                        )}
                    </div>

                    {loading ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-cyber-primary/70 font-mono">
                            <div className="w-12 h-12 border-b-2 border-l-2 border-cyber-primary rounded-full animate-spin mb-4" />
                            Scanning AST nodes...
                        </div>
                    ) : error ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-cyber-danger font-mono text-center px-4">
                            <AlertCircle size={32} className="mb-3 opacity-80" />
                            <span className="text-sm">Scan Failed</span>
                            <span className="text-xs opacity-70 mt-1">{error}</span>
                        </div>
                    ) : hasRun ? (
                        smells.length === 0 ? (
                            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex-1 flex flex-col items-center justify-center text-cyber-success font-mono text-center">
                                <ShieldAlert size={48} className="mb-4 opacity-50" />
                                <span className="text-lg tracking-widest uppercase">Pure Code</span>
                                <span className="text-xs text-gray-400 mt-2">Zero architectural smells detected in selection.</span>
                            </motion.div>
                        ) : (
                            <div className="flex flex-col h-full">
                                {/* Tabs */}
                                <div className="flex gap-1 mb-4 bg-black/30 rounded-lg p-1">
                                    <button
                                        onClick={() => setActiveTab('smells')}
                                        className={clsx(
                                            'flex-1 py-1.5 px-3 rounded-md font-mono text-[11px] uppercase tracking-widest transition-all',
                                            activeTab === 'smells'
                                                ? 'bg-cyber-primary/20 text-cyber-primary border border-cyber-primary/40'
                                                : 'text-gray-500 hover:text-gray-300'
                                        )}
                                    >
                                        Smells ({smells.length})
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('optimized')}
                                        disabled={!showOptimized && !isRefactoring}
                                        className={clsx(
                                            'flex-1 py-1.5 px-3 rounded-md font-mono text-[11px] uppercase tracking-widest transition-all flex items-center justify-center gap-1.5',
                                            activeTab === 'optimized'
                                                ? 'bg-cyber-primary/20 text-cyber-primary border border-cyber-primary/40'
                                                : 'text-gray-500 hover:text-gray-300',
                                            (!showOptimized && !isRefactoring) && 'opacity-40 cursor-not-allowed'
                                        )}
                                    >
                                        {isRefactoring ? (
                                            <><div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" /> Optimizing...</>
                                        ) : (
                                            <><Sparkles size={11} /> Optimized</>
                                        )}
                                    </button>
                                </div>

                                {/* Smells Tab */}
                                {activeTab === 'smells' && (
                                    <div className="space-y-4 flex-1 overflow-y-auto pr-2 pb-4">
                                        {smells.map((s, i) => {
                                            const pct = Math.round(s.confidence * 100);
                                            const savedConf = localStorage.getItem('codeSage_confThreshold');
                                            const thresholdValue = savedConf ? Number(savedConf) : 75;
                                            const isHighRisk = pct > thresholdValue;
                                            return (
                                                <motion.div
                                                    key={i}
                                                    initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}
                                                    className="glass-panel p-4 bg-white/[0.02] border border-white/10 hover:border-cyber-primary/50 transition-colors"
                                                >
                                                    <div className="flex justify-between items-start mb-3">
                                                        <div className="font-medium text-sm text-white">{s.display_name}</div>
                                                        <div className="font-mono text-xs px-2 py-0.5 rounded bg-black/50 border border-white/10 text-gray-400">Line {s.start_line}</div>
                                                    </div>
                                                    <div className="w-full h-1.5 bg-black/50 rounded-full overflow-hidden relative">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${pct}%` }}
                                                            transition={{ duration: 1, ease: "easeOut" }}
                                                            className={clsx("absolute top-0 left-0 h-full", isHighRisk ? "bg-cyber-danger shadow-[0_0_10px_#ff003c]" : "bg-cyber-warning text-cyber-warning")}
                                                        />
                                                    </div>
                                                    <div className="flex justify-between items-center mt-2 font-mono text-[10px] uppercase tracking-wider">
                                                        <span className="text-gray-500">Metric Output: <span className="text-gray-300">{s.metric_value}</span> / {s.threshold} max</span>
                                                        <span className={clsx("font-bold flex gap-2", isHighRisk ? "text-cyber-danger" : "text-cyber-warning")}>
                                                            <span className="text-gray-500 font-normal">CONFIDENCE:</span> {pct}%
                                                        </span>
                                                    </div>
                                                </motion.div>
                                            );
                                        })}
                                        {showOptimized && (
                                            <motion.button
                                                initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                                                onClick={() => setActiveTab('optimized')}
                                                className="w-full mt-2 bg-cyber-primary/10 hover:bg-cyber-primary/20 border border-cyber-primary/40 text-cyber-primary py-2 rounded-lg font-mono text-[11px] tracking-widest uppercase transition-all flex items-center justify-center gap-2"
                                            >
                                                <Sparkles size={13} /> View Optimized Code
                                            </motion.button>
                                        )}
                                    </div>
                                )}

                                {/* Optimized Code Tab */}
                                {activeTab === 'optimized' && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                        className="flex flex-col flex-1 overflow-hidden"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-[10px] font-mono text-cyber-primary/60 uppercase tracking-widest flex items-center gap-1.5">
                                                <Sparkles size={11} /> AI-Optimized Output
                                            </span>
                                            <button
                                                onClick={() => { setCode(optimizedCode); setSyncMessage('✓ Optimized code applied to editor.'); setActiveTab('smells'); }}
                                                className="text-[10px] font-mono bg-cyber-primary/20 hover:bg-cyber-primary/30 border border-cyber-primary/40 text-cyber-primary px-3 py-1 rounded transition-all"
                                            >
                                                Apply to Editor
                                            </button>
                                        </div>
                                        <div className="relative flex-1 overflow-hidden rounded-lg border border-white/10 bg-black/40">
                                            <div className="absolute top-2 left-3 text-[10px] font-mono text-gray-600 pointer-events-none">optimized.py</div>
                                            <pre className="h-full overflow-auto pt-7 pb-4 px-4 text-xs font-mono text-gray-300 leading-relaxed whitespace-pre-wrap">
                                                {optimizedCode}
                                            </pre>
                                        </div>
                                    </motion.div>
                                )}
                            </div>
                        )
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-600 font-mono text-center">
                            <Code2 size={48} className="mb-4 opacity-20" />
                            <span className="text-xs uppercase tracking-widest">Awaiting Input</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
