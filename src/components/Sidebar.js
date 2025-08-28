import React, { useState, useEffect } from 'react';
import { MessageCircle, History, BarChart3, X, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const Sidebar = ({ currentView, setCurrentView, isOpen, setIsOpen, userId }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const menuItems = [
    { id: 'chat', label: 'Chat', icon: MessageCircle },
    { id: 'history', label: 'History', icon: History },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  ];

  const handleSearch = async (term) => {
    if (!term.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await axios.get(`http://localhost:5000/api/search`, {
        params: { user_id: userId, q: term }
      });
      setSearchResults(response.data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      handleSearch(searchTerm);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm, userId]);

  const sidebarContent = (
    <div className="h-full flex flex-col bg-white shadow-xl">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100 transition-colors"
          >
            <X className="h-5 w-5 text-gray-600" />
          </button>
        </div>
        
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search your history..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => {
                  setCurrentView(item.id);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  currentView === item.id
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <item.icon className="h-5 w-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Search Results */}
      {searchTerm && (
        <div className="flex-1 p-4 border-t border-gray-200 overflow-y-auto">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Search Results</h3>
          
          {isSearching ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            </div>
          ) : searchResults.length > 0 ? (
            <div className="space-y-3">
              {searchResults.map((result) => (
                <motion.div
                  key={result.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => {
                    setCurrentView('history');
                    setIsOpen(false);
                  }}
                >
                  <p className="text-sm font-medium text-gray-900 mb-1">
                    {result.query}
                  </p>
                  <p className="text-xs text-gray-600 line-clamp-2">
                    {result.response}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(result.timestamp).toLocaleDateString()}
                  </p>
                </motion.div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-8">
              No results found
            </p>
          )}
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex w-80 flex-shrink-0">
        {sidebarContent}
      </div>

      {/* Mobile Sidebar */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="lg:hidden fixed left-0 top-0 h-full w-80 z-50"
            >
              {sidebarContent}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default Sidebar;