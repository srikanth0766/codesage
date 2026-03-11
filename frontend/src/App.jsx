import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
// Child components
import { Routes, Route, useLocation } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import AuditorPage from './pages/AuditorPage';
import HistoryPage from './pages/HistoryPage';
import HealthPage from './pages/HealthPage';
import TerminalPage from './pages/TerminalPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      // For the floating background blob
      document.documentElement.style.setProperty('--cursor-x', `${e.clientX}px`);
      document.documentElement.style.setProperty('--cursor-y', `${e.clientY}px`);

      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen w-full relative overflow-x-hidden font-sans flex">
      {/* Absolute background elements */}
      <div className="cursor-glow will-change-transform" />

      {/* Grid Pattern overlay */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.03] z-[-1]"
        style={{ backgroundImage: 'linear-gradient(rgba(0, 247, 255, 0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 247, 255, 0.5) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area (Offset by Sidebar width on desktop) */}
      <div className="flex-1 md:ml-64 relative flex flex-col min-h-screen">

        {/* Top Header */}
        <header className="sticky top-0 z-30 border-b border-white/5 bg-cyber-900/60 backdrop-blur-xl transition-all h-20 flex items-center px-8">
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide">CodeSage Command Center</h2>
            <p className="text-xs text-cyber-primary/60 font-mono tracking-widest uppercase">Intelligent Software Analysis</p>
          </div>

          <div className="ml-auto flex gap-4">
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="flex-1 p-6 lg:p-10 relative z-10 w-full max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard mousePosition={mousePosition} />} />
            <Route path="/auditor" element={<AuditorPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/health" element={<HealthPage />} />
            <Route path="/terminal" element={<TerminalPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
