import axios from 'axios';

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers if needed
    const userId = localStorage.getItem('constitution_chatbot_user_id');
    if (userId) {
      config.headers['X-User-ID'] = userId;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 429) {
      console.warn('Rate limit exceeded. Please wait before making another request.');
    } else if (error.response?.status >= 500) {
      console.error('Server error. Please try again later.');
    } else if (error.code === 'ECONNREFUSED') {
      console.error('Cannot connect to server. Please ensure the backend is running.');
    }
    
    return Promise.reject(error);
  }
);

// API functions
export const chatAPI = {
  sendMessage: (query, userId, userClass) => {
    return api.post('/api/chat', {
      query,
      user_id: userId,
      class: userClass,
    });
  },

  submitFeedback: (queryId, score) => {
    return api.post('/api/feedback', {
      query_id: queryId,
      score,
    });
  },

  searchHistory: (userId, searchTerm) => {
    return api.get('/api/search', {
      params: {
        user_id: userId,
        q: searchTerm,
      },
    });
  },
};

export const historyAPI = {
  getHistory: (userId, page = 1, perPage = 10) => {
    return api.get(`/api/history/${userId}`, {
      params: {
        page,
        per_page: perPage,
      },
    });
  },
};

export const analyticsAPI = {
  getMetrics: () => {
    return api.get('/api/metrics');
  },
};

export default api;