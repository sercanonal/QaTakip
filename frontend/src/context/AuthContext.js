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
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkExistingUser();
  }, []);

  const checkExistingUser = async () => {
    const deviceId = getDeviceId();
    
    try {
      // Check if device is already registered
      const response = await api.get(`/auth/check/${deviceId}`);
      setUser(response.data);
      localStorage.setItem("qa_user", JSON.stringify(response.data));
    } catch (error) {
      // Device not registered yet
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const register = async (name) => {
    const deviceId = getDeviceId();
    const response = await api.post("/auth/register", { name, device_id: deviceId });
    const userData = response.data;
    setUser(userData);
    localStorage.setItem("qa_user", JSON.stringify(userData));
    return userData;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("qa_user");
    // Keep device_id for potential re-login
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
