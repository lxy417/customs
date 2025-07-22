import React from 'react';
import { usePermissions } from '../context/PermissionContext';
import { Result, Spin } from 'antd';

const PermissionWrapper = ({ 
  children, 
  permission, 
  permissions, 
  requireAll = true,
  customsCode,
  adminOnly = false,
  fallback = null,
  showForbidden = true 
}) => {
  const { 
    hasPermission, 
    hasAnyPermission, 
    hasAllPermissions, 
    hasCustomsCodeAccess, 
    isAdmin, 
    loading 
  } = usePermissions();

  if (loading) {
    return <Spin size="small" />;
  }

  // 检查管理员权限
  if (adminOnly && !isAdmin()) {
    return showForbidden ? (
      <Result
        status="403"
        title="403"
        subTitle="抱歉，您没有权限访问此页面。"
      />
    ) : (fallback || null);
  }

  // 检查单个权限
  if (permission && !hasPermission(permission)) {
    return showForbidden ? (
      <Result
        status="403"
        title="403"
        subTitle="抱歉，您没有权限访问此功能。"
      />
    ) : (fallback || null);
  }

  // 检查多个权限
  if (permissions && permissions.length > 0) {
    const hasRequiredPermissions = requireAll 
      ? hasAllPermissions(permissions)
      : hasAnyPermission(permissions);
    
    if (!hasRequiredPermissions) {
      return showForbidden ? (
        <Result
          status="403"
          title="403"
          subTitle="抱歉，您没有权限访问此功能。"
        />
      ) : (fallback || null);
    }
  }

  // 检查海关编码权限
  if (customsCode && !hasCustomsCodeAccess(customsCode)) {
    return showForbidden ? (
      <Result
        status="403"
        title="403"
        subTitle={`抱歉，您没有权限访问海关编码 ${customsCode} 的数据。`}
      />
    ) : (fallback || null);
  }

  return children;
};

export default PermissionWrapper;