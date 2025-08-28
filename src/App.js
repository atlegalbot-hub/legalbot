import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ChatInterface from './components/ChatInterface';
import History from './components/History';
import Analytics from './components/Analytics';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import { motion } from 'framer-motion';

function App() {
  const [currentView, setCurrentView] = useState('chat');
  const [userId, setUserId] = useState('');
  const [userClass, setUserClass] = useState('10th');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    // Generate or retrieve user ID
    let storedUserId = localStorage.getItem('constitution_chatbot_user_id');
    if (!storedUserId) {
      storedUserId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('constitution_chatbot_user_id', storedUserId);
    }
    setUserId(storedUserId);

    // Get stored class preference
    const storedClass = localStorage.getItem('user_class');
    if (storedClass) {
      setUserClass(storedClass);
    }
  }, []);

  const handleClassChange = (newClass) => {
    setUserClass(newClass);
    localStorage.setItem('user_class', newClass);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Sidebar 
        currentView={currentView}
        setCurrentView={setCurrentView}
        isOpen={sidebarOpen}
        setIsOpen={setSidebarOpen}
        userId={userId}
      />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          userClass={userClass}
          onClassChange={handleClassChange}
          onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        />
        
        <main className="flex-1 overflow-hidden">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="h-full"
          >
            {currentView === 'chat' && (
              <ChatInterface userId={userId} userClass={userClass} />
            )}
            {currentView === 'history' && (
              <History userId={userId} />
            )}
            {currentView === 'analytics' && (
              <Analytics />
            )}
          </motion.div>
        </main>
      </div>
    </div>
  );
}

export default App;