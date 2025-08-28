import React, { useState, useRef, useEffect } from 'react';
import { Send, ThumbsUp, ThumbsDown, Copy, BookOpen, Loader2, Brain, Search, Layers } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const RAGChatInterface = ({ userId, userClass }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: `🙏 **Namaste! Welcome to Constitution Chatbot with RAG Pipeline**\n\nI'm powered by an advanced **Retrieval-Augmented Generation (RAG)** system that:\n\n🧠 **Retrieves relevant documents** using hybrid search (semantic + keyword)\n📚 **Generates contextual responses** based on retrieved Constitution content\n🎯 **Provides class-specific guidance** for grades 8th-12th\n📊 **Learns continuously** from your feedback\n\n**RAG Features:**\n- 🔍 **Hybrid Search**: Dense vector search + BM25 keyword matching\n- 📖 **Document Chunking**: Intelligent content segmentation\n- ⚡ **Real-time Retrieval**: Fast similarity search\n- 🎯 **Context-Aware**: Relevant document context for accurate answers\n\nAsk me anything about the Indian Constitution!`,
      timestamp: new Date(),
      ragInfo: {
        retrievalMethod: 'Welcome Message',
        relevanceScore: 1.0,
        sources: 0
      }
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showRAGDetails, setShowRAGDetails] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const suggestedQuestions = [
    "Who is the Father of Indian Constitution?",
    "Explain the Fundamental Rights in detail",
    "What is the process of Constitutional amendment?",
    "What does the Preamble of Constitution say?",
    "What are the Directive Principles of State Policy?"
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
        queryId: response.data.query_id,
        ragInfo: {
          retrievalMethod: 'RAG Pipeline',
          relevanceScore: response.data.relevance_score || 0,
          sources: response.data.retrieved_sources || 0,
          processingTime: '< 1s'
        }
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: '❌ Sorry, I encountered an error with the RAG pipeline. Please try again later.',
        timestamp: new Date(),
        isError: true,
        ragInfo: {
          retrievalMethod: 'Error',
          relevanceScore: 0,
          sources: 0
        }
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

  const RAGInfoBadge = ({ ragInfo }) => (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className="inline-flex items-center space-x-2 px-3 py-1 bg-gradient-to-r from-purple-100 to-blue-100 rounded-full text-xs font-medium text-purple-700 border border-purple-200"
    >
      <Brain className="h-3 w-3" />
      <span>RAG Score: {(ragInfo.relevanceScore * 100).toFixed(0)}%</span>
      <Layers className="h-3 w-3" />
      <span>{ragInfo.sources} sources</span>
    </motion.div>
  );

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* RAG Status Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="h-5 w-5" />
            <span className="font-semibold">RAG Pipeline Active</span>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-xs">Hybrid Search Enabled</span>
            </div>
          </div>
          <button
            onClick={() => setShowRAGDetails(!showRAGDetails)}
            className="text-xs px-3 py-1 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
          >
            {showRAGDetails ? 'Hide Details' : 'Show RAG Details'}
          </button>
        </div>
        
        {showRAGDetails && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-3 text-xs space-y-1"
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="font-medium">🔍 Retrieval:</span> FAISS + BM25 Hybrid
              </div>
              <div>
                <span className="font-medium">🧠 Embeddings:</span> SentenceTransformer
              </div>
              <div>
                <span className="font-medium">📚 Documents:</span> Constitution Knowledge Base
              </div>
              <div>
                <span className="font-medium">🎯 Generation:</span> Context-Aware Templates
              </div>
            </div>
          </motion.div>
        )}
      </div>

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
              <div className={`max-w-4xl ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                {message.type === 'bot' && (
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                        <BookOpen className="h-4 w-4 text-white" />
                      </div>
                      <span className="text-sm font-medium text-gray-700">Constitution RAG Bot</span>
                    </div>
                    {message.ragInfo && <RAGInfoBadge ragInfo={message.ragInfo} />}
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
                        strong: ({ children }) => <strong className="font-semibold text-purple-800">{children}</strong>,
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

                {/* RAG Details */}
                {message.type === 'bot' && message.ragInfo && !message.isError && (
                  <div className="mt-2 px-3 py-2 bg-gray-50 rounded-lg text-xs text-gray-600">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <span>
                          <Search className="h-3 w-3 inline mr-1" />
                          Method: {message.ragInfo.retrievalMethod}
                        </span>
                        <span>
                          <Layers className="h-3 w-3 inline mr-1" />
                          Relevance: {(message.ragInfo.relevanceScore * 100).toFixed(1)}%
                        </span>
                        <span>Sources: {message.ragInfo.sources}</span>
                      </div>
                      <span className="text-gray-400">{message.ragInfo.processingTime || '< 1s'}</span>
                    </div>
                  </div>
                )}

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
                        title="Excellent Response"
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
                        title="Poor Response"
                      >
                        <ThumbsDown className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => copyToClipboard(message.content)}
                        className="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
                        title="Copy Response"
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
            <div className="max-w-4xl">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                  <BookOpen className="h-4 w-4 text-white" />
                </div>
                <span className="text-sm font-medium text-gray-700">Constitution RAG Bot</span>
                <div className="inline-flex items-center space-x-1 px-2 py-1 bg-purple-100 rounded-full text-xs text-purple-700">
                  <Brain className="h-3 w-3 animate-pulse" />
                  <span>RAG Processing...</span>
                </div>
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
                <div className="flex items-center space-x-2">
                  <Loader2 className="h-4 w-4 animate-spin text-purple-600" />
                  <span className="text-gray-600">
                    <span className="animate-pulse">Retrieving documents</span>
                    <span className="animate-pulse delay-75">...</span>
                    <span className="animate-pulse delay-150">generating response</span>
                  </span>
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
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            🎯 Try these RAG-optimized questions:
          </h3>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(question)}
                className="px-3 py-2 bg-gradient-to-r from-purple-50 to-blue-50 text-purple-700 rounded-lg text-sm hover:from-purple-100 hover:to-blue-100 transition-all duration-200 border border-purple-200"
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
                placeholder={`Ask about Indian Constitution (Class ${userClass}) - RAG will find the most relevant information...`}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none transition-colors"
                rows="1"
                style={{ minHeight: '48px', maxHeight: '120px' }}
                disabled={isLoading}
              />
              <div className="absolute right-3 top-3 flex items-center space-x-1">
                <Brain className="h-4 w-4 text-purple-500" />
                <span className="text-xs text-purple-600 font-medium">RAG</span>
              </div>
            </div>
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="p-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl hover:from-purple-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        
        {/* RAG Status Footer */}
        <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span>RAG Pipeline Ready</span>
          </div>
          <span>Powered by Hybrid Retrieval + Context Generation</span>
        </div>
      </div>
    </div>
  );
};

export default RAGChatInterface;