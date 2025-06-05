import axios from 'axios';

// Base URL for our Flask backend
const BASE_URL = 'http://127.0.0.1:5000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
  },
});


// ===============================================================
//                    Authentication Services
// ===============================================================

export const authAPI = {
  // User signup
  signup: async (userData) => {
    try {
      const response = await api.post('/auth/signup', userData);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Network error' };
    }
  },

  // User login
  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Network error' };
    }
  },
};

// ===============================================================
//                    Project/Upload Services
// ===============================================================

export const projectAPI = {
  // Upload image file
  uploadImage: async (file, projectName = '', objectType = 'auto', userId = 1) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_name', projectName);
      formData.append('object_type', objectType);
      formData.append('user_id', userId);

      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Upload failed' };
    }
  },

  // Process uploaded project
  processProject: async (projectId) => {
    try {
      const response = await api.post(`/process/${projectId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Processing failed' };
    }
  },

  // Get user's projects
  getUserProjects: async (userId = 1) => {
    try {
      const response = await api.get(`/projects?user_id=${userId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Failed to fetch projects' };
    }
  },

  // Get specific project details
  getProject: async (projectId) => {
    try {
      const response = await api.get(`/projects/${projectId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Failed to fetch project' };
    }
  },

  // Download project file
  downloadProject: async (projectId) => {
    try {
      const response = await api.get(`/projects/${projectId}/download`, {
        responseType: 'blob',
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Download failed' };
    }
  },
};

// ===============================================================
//                    Gallery Services
// ===============================================================

export const galleryAPI = {
  // Get public gallery
  getGallery: async () => {
    try {
      const response = await api.get('/gallery');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Failed to fetch gallery' };
    }
  },
};

// ===============================================================
//                    System Services
// ===============================================================

export const systemAPI = {
  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Health check failed' };
    }
  },

  // Get system statistics
  getStats: async () => {
    try {
      const response = await api.get('/stats');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Failed to fetch stats' };
    }
  },
};

// ===============================================================
//                    Utility Functions
// ===============================================================

// Helper function to handle API errors
export const handleAPIError = (error) => {
  if (error.response) {
    // Server responded with error status
    return error.response.data.error || 'Server error';
  } else if (error.request) {
    // Request was made but no response received
    return 'No response from server. Please check your connection.';
  } else {
    // Something else happened
    return 'An unexpected error occurred';
  }
};

// Helper function to check if server is reachable
export const testConnection = async () => {
  try {
    await systemAPI.healthCheck();
    return true;
  } catch (error) {
    return false;
  }
};

export default api;