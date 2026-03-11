import React from 'react';
import { motion } from 'framer-motion';
import { LayoutDashboard, Bug, History, Activity, Settings, Terminal, ShieldAlert } from 'lucide-react';
import clsx from 'clsx';

import { NavLink } from 'react-router-dom';

const navItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Overview', path: '/' },
    { id: 'auditor', icon: Bug, label: 'Neural Auditor', path: '/auditor' },
    { id: 'history', icon: History, label: 'Sprint History', path: '/history' },
    { id: 'health', icon: Activity, label: 'System Health', path: '/health' },
];

const bottomItems = [
    { id: 'terminal', icon: Terminal, label: 'Terminal', path: '/terminal' },
    { id: 'settings', icon: Settings, label: 'Configuration', path: '/settings' },
];

export default function Sidebar() {
    return (
        <aside className="w-64 h-screen fixed left-0 top-0 hidden md:flex flex-col bg-cyber-900/40 backdrop-blur-xl border-r border-white/5 z-40">

            {/* Brand Logo */}
            <div className="h-20 flex items-center px-6 border-b border-white/5">
                <div className="relative mr-3">
                    <ShieldAlert className="w-8 h-8 text-cyber-primary" />
                    <span className="absolute inset-0 blur-md text-cyber-primary opacity-50"><ShieldAlert /></span>
                </div>
                <div>
                    <h1 className="text-xl font-bold tracking-tight text-white drop-shadow-md">
                        CodeSage <span className="font-light text-cyber-primary">Core</span>
                    </h1>
                </div>
            </div>

            {/* Main Navigation */}
            <nav className="flex-1 py-6 px-4 space-y-2 overflow-y-auto">
                <div className="text-xs font-mono text-gray-500 uppercase tracking-widest px-2 mb-4">Main Menu</div>

                {navItems.map((item) => (
                    <NavLink
                        key={item.id}
                        to={item.path}
                        className={({ isActive }) => clsx(
                            "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300 group relative overflow-hidden",
                            isActive
                                ? "bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/20"
                                : "text-gray-400 hover:bg-white/5 hover:text-white border border-transparent"
                        )}
                    >
                        {({ isActive }) => (
                            <>
                                {isActive && (
                                    <motion.div
                                        layoutId="active-nav"
                                        className="absolute inset-0 bg-cyber-primary/5 border-l-2 border-cyber-primary opacity-50"
                                        initial={false}
                                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                    />
                                )}
                                <item.icon size={18} className="relative z-10" />
                                <span className="font-medium text-sm relative z-10">{item.label}</span>
                            </>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* Bottom Actions */}
            <div className="p-4 border-t border-white/5 space-y-2">
                {bottomItems.map((item) => (
                    <NavLink
                        key={item.id}
                        to={item.path}
                        className={({ isActive }) => clsx(
                            "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300 group relative overflow-hidden",
                            isActive
                                ? "bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/20"
                                : "text-gray-400 hover:bg-white/5 hover:text-white border border-transparent"
                        )}
                    >
                        {({ isActive }) => (
                            <>
                                {isActive && (
                                    <motion.div
                                        layoutId="active-nav-bottom"
                                        className="absolute inset-0 bg-cyber-primary/5 border-l-2 border-cyber-primary opacity-50"
                                        initial={false}
                                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                    />
                                )}
                                <item.icon size={18} className="relative z-10" />
                                <span className="font-medium text-sm relative z-10">{item.label}</span>
                            </>
                        )}
                    </NavLink>
                ))}

                {/* Connection Status Indicator */}
                <div className="mt-4 pt-4 border-t border-white/5 flex items-center gap-3 px-2">
                    <div className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyber-success opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-cyber-success shadow-neon-success"></span>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-xs font-mono text-gray-300">FastAPI Online</span>
                        <span className="text-[10px] text-gray-500 font-mono">127.0.0.1:8000</span>
                    </div>
                </div>
            </div>
        </aside>
    );
}
