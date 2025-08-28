import React, { useState, useRef, useEffect } from 'react';
import { Send, ThumbsUp, ThumbsDown, Copy, BookOpen, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const ChatInterface = ({ userId, userClass }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: `🙏 **Namaste! Welcome to Constitution Chatbot**\n\nI'm here to help you learn about the Indian Constitution and legal system. I'm specially designed for students of classes 8th to 12th.\n\n**What can I help you with today?**\n- 📜 History of Indian Constitution\n- ⚖️ Fundamental Rights and Duties\n- 🏛️ Government Structure\n- 📝 Constitutional Amendments\n- 🎯 Scenario-based questions\n\nFeel free to ask any question about Indian Constitution and law!`,
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const suggestedQuestions = [
    "Who is known as the Father of Indian Constitution?",
    "What are the Fundamental Rights?",
    "Explain the amendment process",
    "What is the Preamble of Indian Constitution?",
    "Difference between Fundamental Rights and Directive Principles"
  ];

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:5000/api/chat', {
        query: inputValue,
        user_id: userId,
        class: userClass
      });

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.data.response,
        timestamp: new Date(),
        queryId: response.data.query_id
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: '❌ Sorry, I encountered an error. Please try again later.',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFeedback = async (messageId, score) => {
    const message = messages.find(m => m.id === messageId);
    if (!message?.queryId) return;

    try {
      await axios.post('http://localhost:5000/api/feedback', {
        query_id: message.queryId,
        score: score
      });

      setMessages(prev => prev.map(m => 
        m.id === messageId 
          ? { ...m, feedback: score }
          : m
      ));
    } catch (error) {
      console.error('Feedback error:', error);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const handleSuggestedQuestion = (question) => {
    setInputValue(question);
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-3xl ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                {message.type === 'bot' && (
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-orange-400 to-red-500 rounded-full flex items-center justify-center">
                      <BookOpen className="h-4 w-4 text-white" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">Constitution Bot</span>
                  </div>
                )}
                
                <div className={`rounded-2xl p-4 ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : message.isError
                    ? 'bg-red-50 border border-red-200'
                    : 'bg-white border border-gray-200 shadow-sm'
                }`}>
                  {message.type === 'bot' ? (
                    <ReactMarkdown 
                      className="prose prose-sm max-w-none"
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold text-blue-800">{children}</strong>,
                        ul: ({ children }) => <ul className="list-disc pl-5 mb-2">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-5 mb-2">{children}</ol>,
                        li: ({ children }) => <li className="mb-1">{children}</li>,
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                </div>

                {message.type === 'bot' && !message.isError && (
                  <div className="flex items-center justify-between mt-2 space-x-2">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleFeedback(message.id, 5)}
                        className={`p-1 rounded-full transition-colors ${
                          message.feedback === 5
                            ? 'bg-green-100 text-green-600'
                            : 'text-gray-400 hover:bg-green-50 hover:text-green-600'
                        }`}
                        title="Helpful"
                      >
                        <ThumbsUp className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleFeedback(message.id, 1)}
                        className={`p-1 rounded-full transition-colors ${
                          message.feedback === 1
                            ? 'bg-red-100 text-red-600'
                            : 'text-gray-400 hover:bg-red-50 hover:text-red-600'
                        }`}
                        title="Not helpful"
                      >
                        <ThumbsDown className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => copyToClipboard(message.content)}
                        className="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
                        title="Copy"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                    </div>
                    <span className="text-xs text-gray-400">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="max-w-3xl">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-8 h-8 bg-gradient-to-r from-orange-400 to-red-500 rounded-full flex items-center justify-center">
                  <BookOpen className="h-4 w-4 text-white" />
                </div>
                <span className="text-sm font-medium text-gray-700">Constitution Bot</span>
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
                <div className="flex items-center space-x-2">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                  <span className="text-gray-600">Thinking...</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length <= 1 && (
        <div className="px-6 py-4 border-t border-gray-200 bg-white">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Suggested Questions:</h3>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(question)}
                className="px-3 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm hover:bg-blue-100 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-6 border-t border-gray-200 bg-white">
        <div className="flex items-end space-x-4">
          <div className="flex-1">
            <div className="relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Ask about Indian Constitution (Class ${userClass})...`}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors"
                rows="1"
                style={{ minHeight: '48px', maxHeight: '120px' }}
                disabled={isLoading}
              />
            </div>
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;