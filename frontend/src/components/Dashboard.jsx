import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import StatCard from './StatCard';
import RiskGauge from './RiskGauge';
import SystemHealth from './SystemHealth';
import ActivityFeed from './ActivityFeed';
import { Activity, Bug, Cpu, Zap, TrendingUp, AlertTriangle } from 'lucide-react';

const BACKEND = 'http://localhost:8000';

export default function Dashboard({ mousePosition }) {
    const [sprints, setSprints] = useState([]);
    const [summary, setSummary] = useState(null);
    const [risk, setRisk] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const res = await fetch(`${BACKEND}/sprint-analytics`);
            if (res.ok) {
                const data = await res.json();
                setSprints(data.sprints);
                setSummary(data.summary);

                if (data.sprints.length >= 2) {
                    const hist = data.sprints.map(s => s.smell_count);
                    const refHist = data.sprints.map(s => s.refactor_count);

                    const savedRisk = localStorage.getItem('codeSage_riskThreshold');
                    const thresholdValue = savedRisk ? Number(savedRisk) : 10;

                    const riskRes = await fetch(`${BACKEND}/predict-sprint-risk`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ sprint_history: hist, refactor_history: refHist, threshold: thresholdValue })
                    });
                    if (riskRes.ok) {
                        const riskData = await riskRes.json();
                        setRisk(riskData);
                    }
                } else {
                    const savedRisk = localStorage.getItem('codeSage_riskThreshold');
                    const thresholdValue = savedRisk ? Number(savedRisk) : 10;
                    setRisk({
                        risk_probability: 0,
                        predicted_smell_count: 0,
                        threshold: thresholdValue,
                        trend: 'stable',
                        recommendation: "Insufficient data. Log at least 2 sprints to predict technical debt drift."
                    });
                }
            }
        } catch (e) {
            console.warn("Backend unavailable falling back to demo data");
            setSummary({ total_sprints: 5, total_smells_detected: 48, total_refactored: 20, average_smell_per_sprint: 9.6, trend: 'increasing' });
            setSprints([
                { sprint_id: 'Sprint-1', smell_count: 5, refactor_count: 2, module: 'demo' },
                { sprint_id: 'Sprint-2', smell_count: 12, refactor_count: 6, module: 'demo' },
            ]);
            const savedRisk = localStorage.getItem('codeSage_riskThreshold');
            const thresholdValue = savedRisk ? Number(savedRisk) : 10;
            setRisk({ risk_probability: 0.85, predicted_smell_count: 15, threshold: thresholdValue, trend: 'rapidly_increasing', recommendation: "CRITICAL ALERT: Refactor immediately." });
        }
    };

    const containerVars = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: { staggerChildren: 0.1 }
        }
    };

    const itemVars = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100 } }
    };

    return (
        <motion.div
            variants={containerVars} initial="hidden" animate="show"
            className="flex flex-col gap-8 pb-24"
        >
            {/* Top row: 4 Stat Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                <motion.div variants={itemVars}>
                    <StatCard title="Total Sprints" value={summary?.total_sprints || 0} icon={<Activity className="text-cyber-primary" />} />
                </motion.div>
                <motion.div variants={itemVars}>
                    <StatCard title="Smells Detected" value={summary?.total_smells_detected || 0} icon={<Bug className="text-cyber-danger" />} />
                </motion.div>
                <motion.div variants={itemVars}>
                    <StatCard title="Smells Refactored" value={summary?.total_refactored || 0} icon={<Zap className="text-cyber-success" />} />
                </motion.div>
                <motion.div variants={itemVars}>
                    <StatCard title="Trend" value={summary?.trend?.replace('_', ' ') || 'stable'} icon={<TrendingUp className="text-cyber-warning" />} isString />
                </motion.div>
            </div>

            {/* Middle Grid: Risk Predictor & System Health & Activity Feed */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

                {/* Left Column: Risk and Health */}
                <div className="xl:col-span-1 flex flex-col gap-8">
                    <motion.div variants={itemVars} className="flex-1">
                        <RiskGauge risk={risk} />
                    </motion.div>
                    <motion.div variants={itemVars} className="flex-1">
                        <SystemHealth />
                    </motion.div>
                </div>

                {/* Right Column: Activity Feed takes up more space */}
                <motion.div variants={itemVars} className="xl:col-span-2 h-full min-h-[600px]">
                    <ActivityFeed />
                </motion.div>
            </div>

        </motion.div>
    );
}
