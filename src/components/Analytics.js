import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, MessageSquare, Star, Brain, Target } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';

const Analytics = () => {
  const [metrics, setMetrics] = useState({
    total_queries: 0,
    average_feedback: 0,
    satisfaction_rate: 0,
    recent_activity: 0,
    learning_progress: { status: 'Loading...', progress: 0 }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30 seconds
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

  const StatCard = ({ icon: Icon, title, value, subtitle, color, trend }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200"
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
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
      <p className="text-sm font-medium text-gray-600">{title}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </motion.div>
  );

  const ProgressBar = ({ percentage, color, label }) => (
    <div className="mb-4">
      <div className="flex justify-between text-sm font-medium text-gray-700 mb-2">
        <span>{label}</span>
        <span>{percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <motion.div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${percentage}%` }}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
    </div>
  );

  const LearningInsight = ({ title, description, status }) => (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
      <div className="flex items-center space-x-2 mb-2">
        <Brain className="h-5 w-5 text-blue-600" />
        <h4 className="font-semibold text-blue-900">{title}</h4>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          status === 'Improving' ? 'bg-green-100 text-green-800' :
          status === 'Stable' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          {status}
        </span>
      </div>
      <p className="text-sm text-blue-700">{description}</p>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <BarChart3 className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          </div>
          <p className="text-gray-600">Monitor chatbot performance and learning optimization</p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={MessageSquare}
            title="Total Queries"
            value={metrics.total_queries.toLocaleString()}
            subtitle="All-time conversations"
            color="bg-blue-500"
            trend={12}
          />
          <StatCard
            icon={Star}
            title="Average Rating"
            value={`${metrics.average_feedback}/5`}
            subtitle="User satisfaction score"
            color="bg-yellow-500"
            trend={5}
          />
          <StatCard
            icon={Target}
            title="Satisfaction Rate"
            value={`${metrics.satisfaction_rate}%`}
            subtitle="4+ star ratings"
            color="bg-green-500"
            trend={8}
          />
          <StatCard
            icon={TrendingUp}
            title="Recent Activity"
            value={metrics.recent_activity.toString()}
            subtitle="Last 7 days"
            color="bg-purple-500"
            trend={-3}
          />
        </div>

        {/* Learning Progress */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white p-6 rounded-xl shadow-sm border border-gray-200"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Brain className="h-5 w-5 mr-2 text-blue-600" />
              AI Learning Progress
            </h3>
            
            <ProgressBar
              percentage={Math.max(0, Math.min(100, 75 + metrics.learning_progress.progress))}
              color="bg-blue-500"
              label="Response Accuracy"
            />
            
            <ProgressBar
              percentage={metrics.satisfaction_rate}
              color="bg-green-500"
              label="User Satisfaction"
            />
            
            <ProgressBar
              percentage={Math.min(100, (metrics.total_queries / 100) * 100)}
              color="bg-purple-500"
              label="Knowledge Base Coverage"
            />

            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>Current Status:</strong> {metrics.learning_progress.status}
              </p>
              <p className="text-xs text-gray-600 mt-1">
                The AI is continuously learning from user interactions to improve response quality.
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
              Optimization Insights
            </h3>
            
            <div className="space-y-4">
              <LearningInsight
                title="Response Quality"
                description="AI responses are improving based on user feedback patterns and interaction data."
                status={metrics.learning_progress.status}
              />
              
              <LearningInsight
                title="Topic Coverage"
                description="Constitution topics are well-covered with strong performance in fundamental rights and duties."
                status="Stable"
              />
              
              <LearningInsight
                title="User Engagement"
                description="Students are actively engaging with complex constitutional concepts."
                status="Improving"
              />
            </div>
          </motion.div>
        </div>

        {/* Performance Indicators */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white p-6 rounded-xl shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <BarChart3 className="h-5 w-5 mr-2 text-indigo-600" />
            Key Performance Indicators
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {Math.round(metrics.average_feedback * 20)}%
                </span>
              </div>
              <h4 className="font-semibold text-gray-900">Answer Accuracy</h4>
              <p className="text-sm text-gray-600">Based on user ratings</p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-3 bg-gradient-to-r from-green-500 to-teal-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {Math.round((metrics.recent_activity / Math.max(1, metrics.total_queries)) * 100)}%
                </span>
              </div>
              <h4 className="font-semibold text-gray-900">Usage Growth</h4>
              <p className="text-sm text-gray-600">Recent activity trend</p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-3 bg-gradient-to-r from-orange-500 to-red-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {Math.round(metrics.satisfaction_rate)}%
                </span>
              </div>
              <h4 className="font-semibold text-gray-900">User Satisfaction</h4>
              <p className="text-sm text-gray-600">Positive feedback rate</p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Analytics;