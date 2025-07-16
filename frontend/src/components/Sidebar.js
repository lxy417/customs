import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button } from 'antd';
import { PieChartOutlined, UserOutlined, ImportOutlined, MenuUnfoldOutlined, MenuFoldOutlined } from '@ant-design/icons';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const { Sider } = Layout;

const AppSidebar = ({ collapsed, setCollapsed }) => {
  const location = useLocation();
  const { user } = useAuth();
  // 从props接收collapsed状态和setCollapsed方法
  // 移除本地响应式逻辑，由父组件控制

  // 确定当前选中的菜单项
  const getSelectedKeys = () => {
    const path = location.pathname;
    if (path.includes('/data-query')) return ['data-query'];
    if (path.includes('/user-management')) return ['user-management'];
    if (path.includes('/import')) return ['import'];
    return ['data-query'];
  };

  // 切换折叠状态
  const toggleCollapsed = () => {
    setCollapsed(!collapsed);
  };

  return (
    <Sider
      width="25%"
      theme="light"
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      className={`app-sidebar ${collapsed ? 'collapsed' : ''}`}
      trigger={null}
    >
      <div className="sidebar-header">
        <h1 className="sidebar-title" style={{ display: collapsed ? 'none' : 'block' }}>海关数据管理系统</h1>
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleCollapsed}
          className="sidebar-trigger"
        />
      </div>
      <Menu
        mode="inline"
        selectedKeys={getSelectedKeys()}
        style={{ height: 'calc(100% - 64px)', borderRight: 0, marginTop: 64 }}
        className="sidebar-menu"
        inlineCollapsed={collapsed}
      >
        <Menu.Item key="data-query" icon={<PieChartOutlined />} className="sidebar-menu-item">
          <Link to="/data-query">数据查询</Link>
        </Menu.Item>

        {user?.is_admin && (
        <Menu.Item key="import" icon={<ImportOutlined />} className="sidebar-menu-item">
          <Link to="/import">数据导入</Link>
        </Menu.Item>
        )}

        {/* 只有管理员可以看到用户管理菜单 */}
        {user?.is_admin && (
          <Menu.Item key="user-management" icon={<UserOutlined />} className="sidebar-menu-item">
            <Link to="/user-management">用户管理</Link>
          </Menu.Item>
        )}
      </Menu>
    </Sider>
  );
};

export default AppSidebar;