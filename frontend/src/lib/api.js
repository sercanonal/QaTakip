import axios from "axios";

// API URL - önce REACT_APP_API_URL, yoksa REACT_APP_BACKEND_URL, yoksa localhost
const API_BASE_URL = process.env.REACT_APP_API_URL 
  || process.env.REACT_APP_BACKEND_URL 
  || "http://localhost:8001";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 120000, // 120 saniye timeout (Jira toplu sorguları için)
});

// Add user_id to requests that need it
api.interceptors.request.use((config) => {
  const savedUser = localStorage.getItem("qa_user");
  if (savedUser) {
    try {
      const user = JSON.parse(savedUser);
      if (config.method === "get" && !config.params?.user_id) {
        config.params = { ...config.params, user_id: user.id };
      }
      if (["post", "put", "delete"].includes(config.method) && !config.params?.user_id) {
        config.params = { ...config.params, user_id: user.id };
      }
    } catch (e) {
      console.error("Error parsing user from localStorage");
    }
  }
  return config;
});

// Response error handler
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Network error veya timeout
    if (!error.response) {
      error.userMessage = "Sunucuya ulaşılamıyor. İnternet bağlantınızı kontrol edin.";
      return Promise.reject(error);
    }
    
    // HTTP error codes
    const status = error.response.status;
    const detail = error.response.data?.detail;
    
    if (status === 400) {
      error.userMessage = detail || "Geçersiz istek";
    } else if (status === 404) {
      error.userMessage = detail || "Kayıt bulunamadı";
    } else if (status === 422) {
      error.userMessage = "Geçersiz veri formatı";
    } else if (status === 500) {
      error.userMessage = "Sunucu hatası. Lütfen daha sonra tekrar deneyin.";
    } else {
      error.userMessage = detail || "Bir hata oluştu";
    }
    
    return Promise.reject(error);
  }
);

export default api;
