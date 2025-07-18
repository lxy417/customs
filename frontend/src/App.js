import { useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Layout, Spin, message } from 'antd';
import { useAuth } from './context/AuthContext';
import Login from './pages/Login';
import DataQuery from './pages/DataQuery';
import UserManagement from './pages/UserManagement';
import Import from './pages/Import';
import Home from './pages/Home';
import NotFound from './pages/NotFound';
import Header from './components/Header';
import './App.css';

const { Content, Footer } = Layout;

// 私有路由组件，需要登录才能访问
const PrivateRoute = ({ element }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!isAuthenticated) {
    // 未登录时重定向到登录页，并记录当前位置以便登录后返回
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return element;
};

// 管理员路由组件，需要管理员权限才能访问
const AdminRoute = ({ element }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!user || !user.is_admin) {
    message.error('没有管理员权限，无法访问该页面');
    return <Navigate to="/data-query" replace />;
  }

  return element;
};

function App() {
  const { isAuthenticated } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const routeLocation = useLocation();
  const isLoginPage = routeLocation.pathname === '/login';

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  return (
    
      <Layout className="site-layout" style={{ minHeight: '100vh' }}>
        {isAuthenticated && <Header toggleSidebar={toggleSidebar} />}
        <Content className={`content-container ${isAuthenticated && !isLoginPage ? 'content-authenticated' : 'content-unauthenticated'}`}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/data-query" element={<PrivateRoute element={<DataQuery />} />} />
            <Route path="/user-management" element={<AdminRoute element={<UserManagement />} />} />
            <Route path="/import" element={<AdminRoute element={<Import />} />} />
            <Route path="/home" element={<PrivateRoute element={<Home />} />} />
            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Content>
        <Footer style={{ textAlign: 'center' }}>海关数据管理系统 ©{new Date().getFullYear()} Created with React & Ant Design</Footer>
      </Layout>
    
  );
}

export default App;