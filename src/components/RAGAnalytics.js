import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Search, Brain, Target, Layers, Zap, Database } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';

const RAGAnalytics = () => {
  const [metrics, setMetrics] = useState({
    total_queries: 0,
    average_feedback: 0,
    average_relevance: 0,
    satisfaction_rate: 0,
    recent_activity: 0,
    rag_performance: {
      retrieval_accuracy: 0,
      generation_quality: 0,
      overall_performance: 0,
      status: 'Loading...'
    },
    learning_progress: { status: 'Loading...', progress: 0 }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/metrics');
      setMetrics(response.data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ icon: Icon, title, value, subtitle, color, trend, ragSpecific = false }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className={`bg-white p-6 rounded-xl shadow-sm border-2 hover:shadow-md transition-all duration-200 ${
        ragSpecific ? 'border-purple-200 bg-gradient-to-br from-purple-50 to-blue-50' : 'border-gray-200'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        {trend && (
          <div className={`flex items-center text-sm ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            <TrendingUp className={`h-4 w-4 mr-1 ${trend < 0 ? 'rotate-180' : ''}`} />
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
        {ragSpecific && (
          <div className="flex items-center text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded-full">
            <Brain className="h-3 w-3 mr-1" />
            <span>RAG</span>
          </div>
        )}
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
      <p className="text-sm font-medium text-gray-600">{title}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </motion.div>
  );

  const ProgressBar = ({ percentage, color, label, showRAGBadge = false }) => (
    <div className="mb-4">
      <div className="flex justify-between items-center text-sm font-medium text-gray-700 mb-2">
        <div className="flex items-center space-x-2">
          <span>{label}</span>
          {showRAGBadge && (
            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">RAG Enhanced</span>
          )}
        </div>
        <span>{percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <motion.div
          className={`h-3 rounded-full ${color} relative overflow-hidden`}
          style={{ width: `${percentage}%` }}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
        </motion.div>
      </div>
    </div>
  );

  const RAGInsight = ({ title, description, status, metric }) => (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-4 rounded-lg border border-purple-200">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Brain className="h-5 w-5 text-purple-600" />
          <h4 className="font-semibold text-purple-900">{title}</h4>
        </div>
        <div className="flex items-center space-x-2">
          {metric && (
            <span className="text-sm font-mono bg-purple-200 text-purple-800 px-2 py-1 rounded">
              {metric}
            </span>
          )}
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            status === 'Excellent' ? 'bg-green-100 text-green-800' :
            status === 'Good' ? 'bg-blue-100 text-blue-800' :
            status === 'Improving' ? 'bg-yellow-100 text-yellow-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {status}
          </span>
        </div>
      </div>
      <p className="text-sm text-purple-700">{description}</p>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading RAG Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg">
              <BarChart3 className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">RAG Analytics Dashboard</h1>
          </div>
          <p className="text-gray-600">Monitor Retrieval-Augmented Generation pipeline performance and optimization</p>
        </div>

        {/* RAG Performance Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={Search}
            title="Retrieval Accuracy"
            value={`${(metrics.rag_performance.retrieval_accuracy * 100).toFixed(1)}%`}
            subtitle="Document relevance score"
            color="bg-purple-500"
            trend={8}
            ragSpecific={true}
          />
          <StatCard
            icon={Brain}
            title="Generation Quality"
            value={`${(metrics.rag_performance.generation_quality * 100).toFixed(1)}%`}
            subtitle="Context-aware responses"
            color="bg-blue-500"
            trend={12}
            ragSpecific={true}
          />
          <StatCard
            icon={Target}
            title="Overall Performance"
            value={`${(metrics.rag_performance.overall_performance * 100).toFixed(1)}%`}
            subtitle="Combined RAG score"
            color="bg-indigo-500"
            trend={6}
            ragSpecific={true}
          />
          <StatCard
            icon={Zap}
            title="Relevance Score"
            value={`${(metrics.average_relevance * 100).toFixed(1)}%`}
            subtitle="Average query relevance"
            color="bg-green-500"
            trend={4}
            ragSpecific={true}
          />
        </div>

        {/* Traditional Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={Database}
            title="Total Queries"
            value={metrics.total_queries.toLocaleString()}
            subtitle="Processed by RAG pipeline"
            color="bg-gray-500"
            trend={15}
          />
          <StatCard
            icon={TrendingUp}
            title="User Satisfaction"
            value={`${metrics.satisfaction_rate}%`}
            subtitle="Positive feedback rate"
            color="bg-yellow-500"
            trend={7}
          />
          <StatCard
            icon={BarChart3}
            title="Average Rating"
            value={`${metrics.average_feedback}/5`}
            subtitle="User feedback score"
            color="bg-red-500"
            trend={3}
          />
          <StatCard
            icon={Layers}
            title="Recent Activity"
            value={metrics.recent_activity.toString()}
            subtitle="Last 7 days"
            color="bg-teal-500"
            trend={-2}
          />
        </div>

        {/* RAG Pipeline Performance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white p-6 rounded-xl shadow-sm border border-gray-200"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Brain className="h-5 w-5 mr-2 text-purple-600" />
              RAG Pipeline Performance
            </h3>
            
            <ProgressBar
              percentage={Math.round(metrics.rag_performance.retrieval_accuracy * 100)}
              color="bg-gradient-to-r from-purple-500 to-purple-600"
              label="Document Retrieval"
              showRAGBadge={true}
            />
            
            <ProgressBar
              percentage={Math.round(metrics.rag_performance.generation_quality * 100)}
              color="bg-gradient-to-r from-blue-500 to-blue-600"
              label="Response Generation"
              showRAGBadge={true}
            />
            
            <ProgressBar
              percentage={Math.round(metrics.rag_performance.overall_performance * 100)}
              color="bg-gradient-to-r from-indigo-500 to-indigo-600"
              label="Overall RAG Score"
              showRAGBadge={true}
            />

            <ProgressBar
              percentage={Math.round(metrics.average_relevance * 100)}
              color="bg-gradient-to-r from-green-500 to-green-600"
              label="Relevance Matching"
              showRAGBadge={true}
            />

            <div className="mt-4 p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
              <p className="text-sm text-purple-700">
                <strong>Pipeline Status:</strong> {metrics.rag_performance.status}
              </p>
              <p className="text-xs text-purple-600 mt-1">
                Hybrid search with dense vector + sparse keyword retrieval active
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white p-6 rounded-xl shadow-sm border border-gray-200"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Target className="h-5 w-5 mr-2 text-green-600" />
              RAG Optimization Insights
            </h3>
            
            <div className="space-y-4">
              <RAGInsight
                title="Retrieval Performance"
                description="Vector similarity search combined with BM25 keyword matching provides excellent document relevance."
                status={metrics.rag_performance.status}
                metric={`${(metrics.rag_performance.retrieval_accuracy * 100).toFixed(1)}%`}
              />
              
              <RAGInsight
                title="Generation Quality"
                description="Context-aware response generation using retrieved Constitution documents ensures accuracy."
                status="Good"
                metric={`${(metrics.rag_performance.generation_quality * 100).toFixed(1)}%`}
              />
              
              <RAGInsight
                title="Hybrid Search"
                description="FAISS vector index + BM25 ranking provides comprehensive semantic and keyword matching."
                status="Active"
                metric="Dense + Sparse"
              />
            </div>
          </motion.div>
        </div>

        {/* Learning Progress with RAG Insights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white p-6 rounded-xl shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <Layers className="h-5 w-5 mr-2 text-indigo-600" />
            RAG Learning & Optimization
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-3 bg-gradient-to-r from-purple-500 to-blue-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {Math.round(metrics.rag_performance.retrieval_accuracy * 100)}%
                </span>
              </div>
              <h4 className="font-semibold text-gray-900">Retrieval Accuracy</h4>
              <p className="text-sm text-gray-600">Document relevance matching</p>
              <div className="mt-2 flex items-center justify-center text-xs text-purple-600">
                <Search className="h-3 w-3 mr-1" />
                <span>FAISS + BM25</span>
              </div>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-3 bg-gradient-to-r from-green-500 to-teal-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {Math.round(metrics.rag_performance.generation_quality * 100)}%
                </span>
              </div>
              <h4 className="font-semibold text-gray-900">Generation Quality</h4>
              <p className="text-sm text-gray-600">Context-aware responses</p>
              <div className="mt-2 flex items-center justify-center text-xs text-green-600">
                <Brain className="h-3 w-3 mr-1" />
                <span>Template-based</span>
              </div>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-3 bg-gradient-to-r from-orange-500 to-red-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {Math.round(metrics.satisfaction_rate)}%
                </span>
              </div>
              <h4 className="font-semibold text-gray-900">User Satisfaction</h4>
              <p className="text-sm text-gray-600">Overall system performance</p>
              <div className="mt-2 flex items-center justify-center text-xs text-orange-600">
                <Target className="h-3 w-3 mr-1" />
                <span>Feedback-driven</span>
              </div>
            </div>
          </div>

          {/* RAG Learning Status */}
          <div className="mt-6 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold text-indigo-900 flex items-center">
                <Brain className="h-4 w-4 mr-2" />
                Learning Progress
              </h4>
              <span className="text-sm text-indigo-600">
                {metrics.learning_progress.status}
              </span>
            </div>
            <p className="text-sm text-indigo-700 mb-3">
              The RAG pipeline continuously improves through user feedback and retrieval performance optimization.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="flex items-center text-indigo-600">
                <Search className="h-3 w-3 mr-1" />
                <span>Semantic search optimization</span>
              </div>
              <div className="flex items-center text-indigo-600">
                <Layers className="h-3 w-3 mr-1" />
                <span>Document chunking refinement</span>
              </div>
              <div className="flex items-center text-indigo-600">
                <Brain className="h-3 w-3 mr-1" />
                <span>Context generation tuning</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default RAGAnalytics;