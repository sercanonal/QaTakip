import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add user_id to requests that need it
api.interceptors.request.use((config) => {
  const savedUser = localStorage.getItem("qa_user");
  if (savedUser) {
    try {
      const user = JSON.parse(savedUser);
      // Add user_id as query param for GET requests
      if (config.method === "get" && !config.params?.user_id) {
        config.params = { ...config.params, user_id: user.id };
      }
      // Add user_id as query param for POST/PUT/DELETE if not in body
      if (["post", "put", "delete"].includes(config.method) && !config.params?.user_id) {
        config.params = { ...config.params, user_id: user.id };
      }
    } catch (e) {
      console.error("Error parsing user from localStorage");
    }
  }
  return config;
});

export default api;
