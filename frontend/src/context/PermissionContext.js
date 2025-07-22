import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../utils/api';

const PermissionContext = createContext();

export const usePermissions = () => {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
};

export const PermissionProvider = ({ children }) => {
  const [userInfo, setUserInfo] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [customsCodes, setCustomsCodes] = useState([]);
  const [loading, setLoading] = useState(true);

  // 权限常量
  const PERMISSIONS = {
    DATA_VIEW: 'data_view',
    DATA_CREATE: 'data_create',
    DATA_UPDATE: 'data_update',
    DATA_DELETE: 'data_delete',
    DATA_EXPORT: 'data_export',
    AI_SEARCH: 'ai_search',
    USER_MANAGE: 'user_manage',
    GROUP_MANAGE: 'group_manage',
    ROLE_MANAGE: 'role_manage'
  };

  // 获取用户信息和权限
  const fetchUserInfo = async () => {
    try {
      setLoading(true);
      const response = await authAPI.getCurrentUser();
      setUserInfo(response);
      setPermissions(response.effective_permissions || []);
      setCustomsCodes(response.effective_customs_codes || []);
    } catch (error) {
      console.error('获取用户信息失败:', error);
      setUserInfo(null);
      setPermissions([]);
      setCustomsCodes([]);
    } finally {
      setLoading(false);
    }
  };

  // 检查是否有特定权限
  const hasPermission = (permission) => {
    if (!userInfo) return false;
    if (userInfo.is_admin) return true; // 管理员拥有所有权限
    return permissions.includes(permission);
  };

  // 检查是否有任一权限
  const hasAnyPermission = (permissionList) => {
    if (!userInfo) return false;
    if (userInfo.is_admin) return true;
    return permissionList.some(permission => permissions.includes(permission));
  };

  // 检查是否有所有权限
  const hasAllPermissions = (permissionList) => {
    if (!userInfo) return false;
    if (userInfo.is_admin) return true;
    return permissionList.every(permission => permissions.includes(permission));
  };

  // 检查是否是管理员
  const isAdmin = () => {
    return userInfo?.is_admin || userInfo?.role_id === 'admin';
  };

  // 检查是否有海关编码访问权限
  const hasCustomsCodeAccess = (customsCode) => {
    if (!userInfo) return false;
    if (userInfo.is_admin) return true;
    if (!customsCodes || customsCodes.length === 0) return true; // 无限制
    return customsCodes.includes(customsCode);
  };

  // 获取用户角色名称
  const getRoleName = () => {
    return userInfo?.role_name || '未知角色';
  };

  // 刷新权限信息
  const refreshPermissions = () => {
    fetchUserInfo();
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, []);

  const value = {
    userInfo,
    permissions,
    customsCodes,
    loading,
    PERMISSIONS,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isAdmin,
    hasCustomsCodeAccess,
    getRoleName,
    refreshPermissions,
    fetchUserInfo
  };

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
};