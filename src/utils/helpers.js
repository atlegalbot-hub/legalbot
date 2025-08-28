// Utility helper functions

/**
 * Generate a unique user ID
 */
export const generateUserId = () => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 9);
  return `user_${timestamp}_${random}`;
};

/**
 * Format date for display
 */
export const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = now - date;
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return 'Today';
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else {
    return date.toLocaleDateString();
  }
};

/**
 * Format time for display
 */
export const formatTime = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

/**
 * Truncate text to specified length
 */
export const truncateText = (text, maxLength = 100) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
};

/**
 * Clean markdown text for display
 */
export const cleanMarkdown = (text) => {
  return text
    .replace(/[*#]/g, '')
    .replace(/\n+/g, ' ')
    .trim();
};

/**
 * Calculate reading time for text
 */
export const calculateReadingTime = (text) => {
  const wordsPerMinute = 200;
  const words = text.split(' ').length;
  const minutes = Math.ceil(words / wordsPerMinute);
  return `${minutes} min read`;
};

/**
 * Extract keywords from text
 */
export const extractKeywords = (text) => {
  const stopWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'];
  
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .split(' ')
    .filter(word => word.length > 3 && !stopWords.includes(word))
    .slice(0, 5);
};

/**
 * Get feedback emoji based on score
 */
export const getFeedbackEmoji = (score) => {
  if (score >= 5) return '🌟';
  if (score >= 4) return '👍';
  if (score >= 3) return '😐';
  if (score >= 2) return '👎';
  if (score >= 1) return '😞';
  return '❓';
};

/**
 * Validate user input
 */
export const validateInput = (text, maxLength = 1000) => {
  if (!text || text.trim().length === 0) {
    return { isValid: false, error: 'Please enter a question' };
  }
  
  if (text.length > maxLength) {
    return { isValid: false, error: `Question is too long (max ${maxLength} characters)` };
  }
  
  return { isValid: true, error: null };
};

/**
 * Copy text to clipboard
 */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    return true;
  }
};

/**
 * Debounce function for search
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Get class-specific learning tips
 */
export const getClassTips = (userClass) => {
  const tips = {
    '8th': [
      'Focus on understanding basic concepts',
      'Remember key personalities and dates',
      'Learn about fundamental rights in simple terms'
    ],
    '9th': [
      'Connect constitutional principles with daily life',
      'Understand the importance of democracy',
      'Study the freedom struggle connection'
    ],
    '10th': [
      'Balance between rights and duties',
      'Understand government structure',
      'Learn about judicial review'
    ],
    '11th': [
      'Analyze federal vs unitary features',
      'Study separation of powers',
      'Understand constitutional amendments'
    ],
    '12th': [
      'Critical analysis of contemporary issues',
      'Compare with other constitutions',
      'Understand challenges and reforms'
    ]
  };
  
  return tips[userClass] || tips['10th'];
};

/**
 * Calculate learning progress
 */
export const calculateProgress = (metrics) => {
  const weights = {
    accuracy: 0.4,
    satisfaction: 0.3,
    engagement: 0.3
  };
  
  const accuracy = (metrics.average_feedback / 5) * 100;
  const satisfaction = metrics.satisfaction_rate;
  const engagement = Math.min(100, (metrics.recent_activity / 10) * 100);
  
  return Math.round(
    accuracy * weights.accuracy +
    satisfaction * weights.satisfaction +
    engagement * weights.engagement
  );
};

/**
 * Export chat history as JSON
 */
export const exportHistory = (history, format = 'json') => {
  const data = history.map(item => ({
    question: item.query,
    answer: item.response,
    timestamp: item.timestamp,
    feedback: item.feedback_score
  }));
  
  const filename = `constitution_chat_history_${new Date().toISOString().split('T')[0]}`;
  
  if (format === 'json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadBlob(blob, `${filename}.json`);
  } else if (format === 'csv') {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, `${filename}.csv`);
  }
};

/**
 * Convert data to CSV format
 */
const convertToCSV = (data) => {
  const headers = ['Question', 'Answer', 'Timestamp', 'Feedback'];
  const csvContent = [
    headers.join(','),
    ...data.map(row => [
      `"${row.question.replace(/"/g, '""')}"`,
      `"${row.answer.replace(/"/g, '""')}"`,
      row.timestamp,
      row.feedback || 'N/A'
    ].join(','))
  ].join('\n');
  
  return csvContent;
};

/**
 * Download blob as file
 */
const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export default {
  generateUserId,
  formatDate,
  formatTime,
  truncateText,
  cleanMarkdown,
  calculateReadingTime,
  extractKeywords,
  getFeedbackEmoji,
  validateInput,
  copyToClipboard,
  debounce,
  getClassTips,
  calculateProgress,
  exportHistory,
};