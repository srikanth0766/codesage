import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings, Sliders, Database, Webhook, Key } from 'lucide-react';

export default function SettingsPage() {
    const [riskThreshold, setRiskThreshold] = useState(10);
    const [confidenceThreshold, setConfidenceThreshold] = useState(85);

    useEffect(() => {
        const savedRisk = localStorage.getItem('codeSage_riskThreshold');
        if (savedRisk) setRiskThreshold(Number(savedRisk));

        const savedConf = localStorage.getItem('codeSage_confThreshold');
        if (savedConf) setConfidenceThreshold(Number(savedConf));
    }, []);

    const handleUpdateParameters = () => {
        localStorage.setItem('codeSage_riskThreshold', riskThreshold);
        localStorage.setItem('codeSage_confThreshold', confidenceThreshold);
        alert('Parameters updated successfully!');
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
                    <Settings size={32} />
                </div>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white drop-shadow-md">
                        System Configuration
                    </h1>
                    <p className="text-sm text-gray-400 font-mono mt-1">
                        Global settings and threshold configurations for the CodeSage engine.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

                {/* API Settings */}
                <div className="glass-panel p-6 border-t-white/10 border-l-white/10">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                        <Webhook size={16} className="text-cyber-primary" /> API Configuration
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <label className="text-xs text-gray-400 font-mono uppercase tracking-widest mb-1 block">Backend URL</label>
                            <input type="text" defaultValue="http://localhost:8000" className="w-full bg-black/40 border border-white/10 rounded-lg p-2.5 text-sm font-mono text-gray-300 focus:outline-none focus:border-cyber-primary/50 transition-colors" />
                        </div>
                        <div>
                            <label className="text-xs text-gray-400 font-mono uppercase tracking-widest mb-1 block">Authentication Token</label>
                            <div className="relative">
                                <input type="password" defaultValue="*****************" className="w-full bg-black/40 border border-white/10 rounded-lg p-2.5 text-sm font-mono text-gray-300 focus:outline-none focus:border-cyber-primary/50 transition-colors pr-10" />
                                <Key size={14} className="absolute right-3 top-3 text-gray-500" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Model Thresholds */}
                <div className="glass-panel p-6 border-t-white/10 border-l-white/10">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                        <Sliders size={16} className="text-cyber-primary" /> Model Thresholds
                    </h3>
                    <div className="space-y-6">
                        <div>
                            <div className="flex justify-between mb-1">
                                <label className="text-xs text-gray-400 font-mono uppercase tracking-widest">Risk Tolerance Limit</label>
                                <span className="text-xs text-cyber-warning font-mono">{riskThreshold} Smells</span>
                            </div>
                            <input
                                type="range" min="1" max="50"
                                value={riskThreshold}
                                onChange={(e) => setRiskThreshold(e.target.value)}
                                className="w-full accent-cyber-warning h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                            />
                        </div>
                        <div>
                            <div className="flex justify-between mb-1">
                                <label className="text-xs text-gray-400 font-mono uppercase tracking-widest">Confidence Threshold</label>
                                <span className="text-xs text-cyber-success font-mono">{confidenceThreshold}%</span>
                            </div>
                            <input
                                type="range" min="50" max="99"
                                value={confidenceThreshold}
                                onChange={(e) => setConfidenceThreshold(e.target.value)}
                                className="w-full accent-cyber-success h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                            />
                        </div>
                        <button
                            onClick={handleUpdateParameters}
                            className="cyber-button w-full mt-4 flex items-center justify-center gap-2 text-sm pt-2"
                        >
                            <Database size={14} /> Update Parameters
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
