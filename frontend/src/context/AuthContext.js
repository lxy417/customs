import React, { createContext, useState, useEffect, useContext } from 'react';
import { authAPI } from '../utils/api';
import { message } from 'antd';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // 初始化：检查本地存储的token并验证
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await authAPI.getCurrentUser();
          setUser(response);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Token验证失败:', error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  // 登录
  const login = async (username, password) => {
    try {
      setLoading(true);
      const response = await authAPI.login(username, password);
      const { access_token } = response;
      debugger
      // 保存token并设置默认请求头
      localStorage.setItem('token', access_token);

      // 获取用户信息
      const userResponse = await authAPI.getCurrentUser();
      setUser(userResponse);
      setIsAuthenticated(true);
      message.success('登录成功');
      return true;
    } catch (error) {
      console.error('登录失败:', error);
      message.error(error.response?.data?.detail || '登录失败，请检查用户名和密码');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // 登出
  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('登出请求失败:', error);
    } finally {
      // 清除本地存储和状态
      localStorage.removeItem('token');
      setUser(null);
      setIsAuthenticated(false);
      message.success('已成功登出');
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// 自定义hook，方便组件使用认证上下文
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;