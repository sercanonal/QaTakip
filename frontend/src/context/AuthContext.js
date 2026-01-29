import { createContext, useContext, useState, useEffect } from "react";
import api from "../lib/api";

const AuthContext = createContext(null);

// Generate unique device ID
const getDeviceId = () => {
  let deviceId = localStorage.getItem("qa_device_id");
  if (!deviceId) {
    deviceId = crypto.randomUUID();
    localStorage.setItem("qa_device_id", deviceId);
  }
  return deviceId;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  // Initialize user from localStorage immediately to avoid flash
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("qa_user");
    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch {
        return null;
      }
    }
    return null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkExistingUser();
  }, []);

  const checkExistingUser = async () => {
    const deviceId = getDeviceId();
    const savedUser = localStorage.getItem("qa_user");
    
    // If we have a saved user, verify it's still valid
    if (savedUser) {
      try {
        const response = await api.get(`/auth/check/${deviceId}`);
        setUser(response.data);
        localStorage.setItem("qa_user", JSON.stringify(response.data));
      } catch (error) {
        // Session expired or device not registered - clear local storage
        setUser(null);
        localStorage.removeItem("qa_user");
      }
    }
    
    setLoading(false);
  };

  const register = async (username) => {
    const deviceId = getDeviceId();
    
    // Simple device-based registration - username only
    const response = await api.post("/auth/register", { 
      name: username.trim(),
      device_id: deviceId 
    });
    
    const userData = response.data;
    setUser(userData);
    localStorage.setItem("qa_user", JSON.stringify(userData));
    return userData;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("qa_user");
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem("qa_user", JSON.stringify(updatedUser));
  };

  return (
    <AuthContext.Provider value={{ user, register, logout, updateUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
