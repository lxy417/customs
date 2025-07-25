import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spin, message } from 'antd';
import { useAuth } from '../context/AuthContext';
import { createPermissionChecker, ROUTE_PERMISSIONS } from '../utils/permissions';

// 权限路由组件
const PermissionRoute = ({ element, path, requiredPermissions, fallbackPath = '/new-home' }) => {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // 加载中显示
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  // 未登录重定向到登录页
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 获取路由权限要求
  const routePermissions = requiredPermissions || ROUTE_PERMISSIONS[path] || [];
  
  // 检查权限
  const permissionChecker = createPermissionChecker(user);
  
  if (!permissionChecker.canAccessRoute(routePermissions)) {
    message.error('您没有权限访问该页面');
    return <Navigate to={fallbackPath} replace />;
  }

  return element;
};

// 私有路由组件（需要登录）
export const PrivateRoute = ({ element, path, requiredPermissions, fallbackPath }) => {
  return (
    <PermissionRoute 
      element={element} 
      path={path}
      requiredPermissions={requiredPermissions}
      fallbackPath={fallbackPath}
    />
  );
};

// 管理员路由组件（向后兼容）
export const AdminRoute = ({ element, fallbackPath = '/home' }) => {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const permissionChecker = createPermissionChecker(user);
  
  if (!permissionChecker.isAdmin()) {
    message.error('需要管理员权限才能访问该页面');
    return <Navigate to={fallbackPath} replace />;
  }

  return element;
};

export default PermissionRoute;