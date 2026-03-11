import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Archive, ServerCrash, Plus, X, Trash } from 'lucide-react';
const BACKEND = 'http://localhost:8000';

export default function SprintTable({ sprints, onRefresh }) {
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        sprint_id: '',
        smell_count: 0,
        refactor_count: 0,
        module: 'default'
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            const res = await fetch(`${BACKEND}/log-sprint`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sprint_id: formData.sprint_id,
                    smell_count: parseInt(formData.smell_count),
                    refactor_count: parseInt(formData.refactor_count),
                    module: formData.module
                })
            });
            if (res.ok) {
                setShowForm(false);
                setFormData({ sprint_id: '', smell_count: 0, refactor_count: 0, module: 'default' });
                onRefresh();
            }
        } catch (e) {
            console.error("Failed to add sprint", e);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async (sprintId) => {
        if (!window.confirm("Are you sure you want to delete this sprint record?")) return;

        try {
            const res = await fetch(`${BACKEND}/sprints/${sprintId}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                onRefresh();
            }
        } catch (e) {
            console.error("Failed to delete sprint", e);
        }
    };

    return (
        <div className="glass-panel h-full flex flex-col border-t-white/10 border-l-white/10">
            <div className="p-6 border-b border-white/5 flex justify-between items-center">
                <div>
                    <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                        Sprint Manifest
                    </h2>
                    <div className="text-xs text-gray-400 font-mono tracking-widest mt-1 uppercase">Historical Debt Trajectory</div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setShowForm(!showForm)}
                        className="cyber-button text-xs py-2 px-4 flex items-center gap-2 bg-cyber-primary/20 hover:bg-cyber-primary/30"
                    >
                        {showForm ? <X size={14} /> : <Plus size={14} />}
                        {showForm ? 'Cancel' : 'Add Sprint'}
                    </button>
                    <button
                        onClick={onRefresh}
                        className="cyber-button text-xs py-2 px-4 flex items-center gap-2"
                    >
                        <Activity size={14} /> Synchronize
                    </button>
                </div>
            </div>

            <AnimatePresence>
                {showForm && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden border-b border-white/5 bg-black/20"
                    >
                        <form onSubmit={handleSubmit} className="p-6 grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
                            <div>
                                <label className="block text-xs font-mono text-gray-400 mb-1 uppercase tracking-wider">Sprint ID</label>
                                <input required type="text" value={formData.sprint_id} onChange={e => setFormData({ ...formData, sprint_id: e.target.value })} className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyber-primary focus:outline-none" placeholder="Sprint-X" />
                            </div>
                            <div>
                                <label className="block text-xs font-mono text-gray-400 mb-1 uppercase tracking-wider">Smells Detected</label>
                                <input required type="number" min="0" value={formData.smell_count} onChange={e => setFormData({ ...formData, smell_count: e.target.value })} className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyber-primary focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs font-mono text-gray-400 mb-1 uppercase tracking-wider">Refactored</label>
                                <input required type="number" min="0" value={formData.refactor_count} onChange={e => setFormData({ ...formData, refactor_count: e.target.value })} className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyber-primary focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs font-mono text-gray-400 mb-1 uppercase tracking-wider">Module</label>
                                <input required type="text" value={formData.module} onChange={e => setFormData({ ...formData, module: e.target.value })} className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyber-primary focus:outline-none" />
                            </div>
                            <div>
                                <button type="submit" disabled={isSubmitting} className="w-full cyber-button py-2 flex items-center justify-center gap-2 h-[38px]">
                                    {isSubmitting ? 'Saving...' : 'Save Draft'}
                                </button>
                            </div>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="flex-1 p-0 overflow-hidden relative">
                <div className="absolute inset-0 overflow-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="sticky top-0 bg-cyber-900/90 backdrop-blur-md z-10 text-xs uppercase tracking-widest text-gray-400 font-mono border-b border-white/5">
                            <tr>
                                <th className="py-4 px-6 font-medium">Sprint ID</th>
                                <th className="py-4 px-6 font-medium">Detected</th>
                                <th className="py-4 px-6 font-medium">Refactored</th>
                                <th className="py-4 px-6 font-medium">Net Debt</th>
                                <th className="py-4 px-6 font-medium text-center">Status</th>
                                <th className="py-4 px-6 font-medium text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5 font-mono text-sm">
                            {sprints.length === 0 ? (
                                <tr><td colSpan="5" className="text-center py-12 text-gray-500">No sprint data found. Awaiting telemetry.</td></tr>
                            ) : (
                                sprints.map((s, i) => {
                                    const net = s.smell_count - s.refactor_count;
                                    const isDanger = net > 15;
                                    const isWarn = net > 8 && !isDanger;

                                    return (
                                        <motion.tr
                                            key={s.sprint_id}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.05 }}
                                            className="group hover:bg-white/[0.02] transition-colors cursor-default"
                                        >
                                            <td className="py-4 px-6 text-white group-hover:text-cyber-primary transition-colors flex items-center gap-3">
                                                <Archive size={14} className="text-gray-500 group-hover:text-cyber-primary" />
                                                {s.sprint_id}
                                            </td>
                                            <td className="py-4 px-6 text-gray-300">{s.smell_count}</td>
                                            <td className="py-4 px-6 text-cyber-success">{s.refactor_count}</td>
                                            <td className={`py-4 px-6 ${isDanger ? 'text-cyber-danger' : isWarn ? 'text-cyber-warning' : 'text-gray-400'}`}>
                                                {net > 0 ? '+' : ''}{net}
                                            </td>
                                            <td className="py-4 px-6 flex justify-center">
                                                <div className={`w-2 h-2 rounded-full ${isDanger ? 'bg-cyber-danger shadow-neon-primary' : isWarn ? 'bg-cyber-warning' : 'bg-cyber-success'}`} />
                                            </td>
                                            <td className="py-4 px-6 text-center">
                                                <button
                                                    onClick={() => handleDelete(s.sprint_id)}
                                                    className="p-1.5 text-gray-500 hover:text-cyber-danger hover:bg-cyber-danger/10 rounded transition-colors"
                                                    title="Delete Sprint"
                                                >
                                                    <Trash size={14} />
                                                </button>
                                            </td>
                                        </motion.tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
