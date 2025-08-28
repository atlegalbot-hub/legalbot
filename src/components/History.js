import React, { useState, useEffect } from 'react';
import { Clock, Search, Download, Trash2, MessageCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const History = ({ userId }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, [userId, currentPage, searchTerm]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:5000/api/history/${userId}`, {
        params: {
          page: currentPage,
          per_page: 10,
          search: searchTerm
        }
      });
      setHistory(response.data.history || []);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      console.error('Error fetching history:', error);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  const exportHistory = () => {
    const exportData = history.map(item => ({
      query: item.query,
      response: item.response,
      timestamp: item.timestamp,
      feedback_score: item.feedback_score
    }));
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `constitution_chat_history_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
  };

  const getFeedbackIcon = (score) => {
    if (score >= 4) return '👍';
    if (score >= 3) return '😐';
    if (score >= 1) return '👎';
    return '❓';
  };

  const truncateText = (text, maxLength = 100) => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Clock className="h-6 w-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">Chat History</h1>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={exportHistory}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search your conversations..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex">
        {/* History List */}
        <div className="w-1/2 border-r border-gray-200 bg-white">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : history.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {history.map((item, index) => {
                const { date, time } = formatDate(item.timestamp);
                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedItem?.id === item.id ? 'bg-blue-50 border-r-2 border-blue-600' : ''
                    }`}
                    onClick={() => setSelectedItem(item)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {item.query}
                        </p>
                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                          {truncateText(item.response.replace(/[*#]/g, ''))}
                        </p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-400">
                            {date} at {time}
                          </span>
                          <span className="text-lg">
                            {getFeedbackIcon(item.feedback_score)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <MessageCircle className="h-12 w-12 mb-4" />
              <p className="text-lg font-medium">No conversations yet</p>
              <p className="text-sm">Start chatting to see your history here</p>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2 p-4 border-t border-gray-200">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </div>

        {/* Detail View */}
        <div className="flex-1 bg-gray-50">
          {selectedItem ? (
            <div className="h-full overflow-y-auto">
              <div className="p-6">
                <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">Question</h2>
                    <span className="text-sm text-gray-500">
                      {formatDate(selectedItem.timestamp).date} at {formatDate(selectedItem.timestamp).time}
                    </span>
                  </div>
                  <p className="text-gray-700 bg-gray-50 p-4 rounded-lg">
                    {selectedItem.query}
                  </p>
                </div>

                <div className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">Answer</h2>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">Feedback:</span>
                      <span className="text-lg">{getFeedbackIcon(selectedItem.feedback_score)}</span>
                    </div>
                  </div>
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold text-blue-800">{children}</strong>,
                        ul: ({ children }) => <ul className="list-disc pl-5 mb-3">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-5 mb-3">{children}</ol>,
                        li: ({ children }) => <li className="mb-1">{children}</li>,
                      }}
                    >
                      {selectedItem.response}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <MessageCircle className="h-12 w-12 mx-auto mb-4" />
                <p className="text-lg font-medium">Select a conversation</p>
                <p className="text-sm">Choose a chat from the left to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default History;