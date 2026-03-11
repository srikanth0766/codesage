import React from 'react';
import { motion } from 'framer-motion';
import SystemHealth from '../components/SystemHealth';
import ActivityFeed from '../components/ActivityFeed';
import { Activity } from 'lucide-react';

export default function HealthPage() {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="flex flex-col gap-8 pb-24 h-full"
        >
            <div className="flex items-center gap-4 border-b border-white/5 pb-6">
                <div className="p-3 rounded-xl bg-cyber-success/10 border border-cyber-success/20 text-cyber-success shadow-neon-success">
                    <Activity size={32} />
                </div>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white drop-shadow-md">
                        System Health
                    </h1>
                    <p className="text-sm text-gray-400 font-mono mt-1">
                        Live telemetry and operational status of the CodeSage analytical engine.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 min-h-[400px]">
                <SystemHealth />
                <ActivityFeed />
            </div>
        </motion.div>
    );
}
