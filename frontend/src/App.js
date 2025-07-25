import { useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Layout, Spin } from 'antd';
import { useAuth } from './context/AuthContext';
import { PrivateRoute } from './components/PermissionRoute';
import { PERMISSIONS } from './utils/permissions';
import Login from './pages/Login';
import DataQuery from './pages/DataQuery';
import UserManagement from './pages/UserManagement';
import ConfigManagement from './pages/ConfigManagement';
import Home from './pages/Home';
import NewHome from './pages/NewHome';
import NotFound from './pages/NotFound';
import Header from './components/Header';
import './App.css';
import EnhancedImport from './pages/EnhancedImport';

const { Content, Footer } = Layout;

function App() {
  const { isAuthenticated } = useAuth();
  const routeLocation = useLocation();
  const isLoginPage = routeLocation.pathname === '/login';

  return (
    <Layout className="site-layout" style={{ minHeight: '100vh' }}>
      {isAuthenticated && <Header />}
      <Content style={{height: "100vh"}} className={`content-container ${isAuthenticated && !isLoginPage ? 'content-authenticated' : 'content-unauthenticated'}`}>
        <Routes> 
          {/* 登录页面 - 如果已登录则重定向到首页 */}
          <Route 
            path="/login" 
            element={isAuthenticated ? <Navigate to="/new-home" replace /> : <Login />} 
          />
          
          {/* 新首页 - 需要登录但无特殊权限要求 */}
          <Route 
            path="/new-home" 
            element={
              <PrivateRoute 
                element={<NewHome />} 
                path="/new-home"
              />
            } 
          />
          
          {/* 原首页 - 保留作为备用 */}
          <Route 
            path="/home" 
            element={
              <PrivateRoute 
                element={<Home />} 
                path="/home"
              />
            } 
          />
          
          {/* 数据查询 - 需要 data_view 权限 */}
          <Route 
            path="/data-query" 
            element={
              <PrivateRoute 
                element={<DataQuery />} 
                path="/data-query"
                requiredPermissions={[PERMISSIONS.DATA_VIEW]}
              />
            } 
          />
          
          {/* 批量导入 - 需要 data_import 权限 */}
          <Route 
            path="/import" 
            element={
              <PrivateRoute 
                element={<EnhancedImport />} 
                path="/import"
                requiredPermissions={[PERMISSIONS.DATA_IMPORT]}
              />
            } 
          />
          
          {/* 用户管理 - 需要任意一个管理权限 */}
          <Route 
            path="/user-management" 
            element={
              <PrivateRoute 
                element={<UserManagement />} 
                path="/user-management"
                requiredPermissions={[PERMISSIONS.USER_MANAGE, PERMISSIONS.ROLE_MANAGE, PERMISSIONS.GROUP_MANAGE]}
              />
            } 
          />
          
          {/* 配置管理 - 需要 config_view 权限 */}
          <Route 
            path="/config-management" 
            element={
              <PrivateRoute 
                element={<ConfigManagement />} 
                path="/config-management"
                requiredPermissions={[PERMISSIONS.CONFIG_VIEW]}
              />
            } 
          />
          
          {/* 默认重定向到首页 */}
          <Route path="/" element={<Navigate to="/new-home" replace />} />
          
          {/* 404页面 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Content>
      {/* <Footer style={{ textAlign: 'center' }}>精算平台 ©{new Date().getFullYear()} Created with React & Ant Design</Footer> */}
    </Layout>
  );
}

export default App;