import React from 'react';
import { Menu, GraduationCap, BookOpen } from 'lucide-react';
import { motion } from 'framer-motion';

const Header = ({ userClass, onClassChange, onMenuClick }) => {
  const classes = ['8th', '9th', '10th', '11th', '12th'];

  return (
    <motion.header 
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-white shadow-lg border-b border-gray-200"
    >
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100 transition-colors"
          >
            <Menu className="h-6 w-6 text-gray-600" />
          </button>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-orange-400 to-red-500 rounded-xl">
              <BookOpen className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Constitution Chatbot</h1>
              <p className="text-sm text-gray-600">Learn Indian Constitution & Law</p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <GraduationCap className="h-5 w-5 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Class:</span>
            <select
              value={userClass}
              onChange={(e) => onClassChange(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium bg-white hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            >
              {classes.map(cls => (
                <option key={cls} value={cls}>{cls}</option>
              ))}
            </select>
          </div>
          
          <div className="hidden sm:flex items-center space-x-2 text-sm text-gray-600">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>AI Learning Active</span>
          </div>
        </div>
      </div>
    </motion.header>
  );
};

export default Header;