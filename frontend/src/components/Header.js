import { Layout, Dropdown, Menu, Avatar, Typography, Space } from 'antd';
import { PieChartOutlined, ImportOutlined, UserOutlined, LogoutOutlined, SettingOutlined, CloudUploadOutlined } from '@ant-design/icons';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePermissions, PERMISSIONS } from '../utils/permissions';
import './Header.css';

const { Header } = Layout;

const AppHeader = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const { hasPermission } = usePermissions(user);

  // 用户菜单选项
  const userMenu = (
    <Menu
      items={[
        {
          key: 'profile',
          icon: <UserOutlined />,
          label: user?.username,
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
    if (path.includes('/import')) return ['enhanced-import'];
    if (path.includes('/home')) return ['home'];
    return ['home'];
  };

  // 构建菜单项数组
  const getMenuItems = () => {
    const menuItems = [];

    // 首页 - 所有用户都可以访问
    menuItems.push({
      key: 'home',
      icon: <PieChartOutlined />,
      label: <Link to="/home">首页</Link>,
    });

    // 数据查询 - 需要 data_view 权限
    if (hasPermission(PERMISSIONS.DATA_VIEW)) {
      menuItems.push({
        key: 'data-query',
        icon: <PieChartOutlined />,
        label: <Link to="/data-query">数据查询</Link>,
      });
    }

    // 批量导入 - 需要 data_import 权限
    if (hasPermission(PERMISSIONS.DATA_IMPORT)) {
      menuItems.push({
        key: 'import',
        icon: <CloudUploadOutlined />,
        label: <Link to="/import">批量导入</Link>,
      });
    }

    // 用户管理 - 需要任意一个管理权限
    if (hasPermission(PERMISSIONS.USER_MANAGE) || 
        hasPermission(PERMISSIONS.ROLE_MANAGE) || 
        hasPermission(PERMISSIONS.GROUP_MANAGE)) {
      menuItems.push({
        key: 'user-management',
        icon: <UserOutlined />,
        label: <Link to="/user-management">用户管理</Link>,
      });
    }

    return menuItems;
  };

  return (
    <Header className="app-header">
      <Menu
        mode="horizontal"
        selectedKeys={getSelectedKeys()}
        defaultSelectedKeys={['home']}
        style={{ flex: 1, minWidth: 0 }}
        items={getMenuItems()}
      />
      <div className="header-right">
        <Space size="large">
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