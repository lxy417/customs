import { Layout, Dropdown, Menu, Avatar, Typography, Space } from 'antd';
import { PieChartOutlined, ImportOutlined, UserOutlined, LogoutOutlined, SettingOutlined } from '@ant-design/icons';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Header.css';

const { Header } = Layout;

const AppHeader = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  // 用户菜单选项
  const userMenu = (
    <Menu
      items={[
        {
          key: 'profile',
          icon: <UserOutlined />,
          label: user?.username,
          // disabled: true,
        },
        {
          key: 'setting',
          icon: <SettingOutlined />,
          label: '设置',
          disabled: true,
        },
        {
          type: 'divider',
        },
        {
          key: 'logout',
          icon: <LogoutOutlined />,
          label: '退出登录',
          onClick: logout,
        },
      ]}
    />
  );
  // 确定当前选中的菜单项
  const getSelectedKeys = () => {
    const path = location.pathname;
    if (path.includes('/data-query')) return ['data-query'];
    if (path.includes('/user-management')) return ['user-management'];
    if (path.includes('/import')) return ['import'];
    if (path.includes('/home')) return ['home'];
    return ['home'];
  };
  return (
    <Header className="app-header">
      {/* <Title level={5} className="app-title">海关公司数据</Title> */}
      <Menu
        mode="horizontal"
        selectedKeys={getSelectedKeys()}
        defaultSelectedKeys={['data-query']}
        style={{ flex: 1, minWidth: 0 }}
        // className="sidebar-menu"
      >
        <Menu.Item key="home" icon={<PieChartOutlined />} className="sidebar-menu-item">
          <Link to="/home">首页</Link>
        </Menu.Item>

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
      <div className="header-right">
        <Space size="large">
          {/* <Badge count={0} showZero className="header-notification">
            <BellOutlined className="notification-icon" />
          </Badge> */}
          <Dropdown overlay={userMenu} placement="bottomRight" arrow>
            <div className="user-info" onClick={(e) => e.preventDefault()}>
              <Avatar icon={<UserOutlined />} className="user-avatar" />
              <span className="username">{user?.username}</span>
            </div>
          </Dropdown>
        </Space>
      </div>
    </Header>
  );
};

export default AppHeader;