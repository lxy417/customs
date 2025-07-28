import { Layout, Dropdown, Menu, Avatar, Typography, Space, Button } from 'antd';
import { PieChartOutlined, ImportOutlined, UserOutlined, LogoutOutlined, SettingOutlined, CloudUploadOutlined, ControlOutlined, HomeOutlined, LoginOutlined } from '@ant-design/icons';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePermissions, PERMISSIONS } from '../utils/permissions';
import './Header.css';

const { Header } = Layout;
const { Title } = Typography;

const AppHeader = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
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
    if (path.includes('/config-management')) return ['config-management'];
    if (path.includes('/import')) return ['enhanced-import'];
    if (path.includes('/new-home')) return ['new-home'];
    if (path.includes('/home')) return ['home'];
    return ['home'];
  };

  // 构建菜单项数组
  const getMenuItems = () => {
    const menuItems = [];
    // menuItems.push({
    //   key: 'home',
    //   icon: <HomeOutlined />,
    //   label: <Link to="/home">首页</Link>,
    // });

    // 新首页 - 所有用户都可以访问（包括未登录用户）
    menuItems.push({
      key: 'new-home',
      icon: <HomeOutlined />,
      label: <Link to="/new-home">首页</Link>,
    });

    // 只有登录用户才显示以下菜单项
    if (isAuthenticated) {
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

      // 配置管理 - 需要 config_view 权限
      if (hasPermission(PERMISSIONS.CONFIG_VIEW)) {
        menuItems.push({
          key: 'config-management',
          icon: <ControlOutlined />,
          label: <Link to="/config-management">配置管理</Link>,
        });
      }
    }

    return menuItems;
  };

  return (
    <Header className="app-header">
      <div className="header-left">
        <Title level={3} style={{ color: '#001529', margin: 0 }}>星络</Title>
      </div>
      <Menu
        mode="horizontal"
        selectedKeys={getSelectedKeys()}
        defaultSelectedKeys={['new-home']}
        style={{ flex: 1, minWidth: 0 }}
        items={getMenuItems()}
      />
      <div className="header-right">
        <Space size="large">
          {isAuthenticated ? (
            <Dropdown overlay={userMenu} placement="bottomRight" arrow>
              <div className="user-info" onClick={(e) => e.preventDefault()}>
                <Avatar icon={<UserOutlined />} className="user-avatar" />
                <span className="username">{user?.username}</span>
              </div>
            </Dropdown>
          ) : (
            <Button 
              type="primary" 
              icon={<LoginOutlined />}
              onClick={() => navigate('/login')}
            >
              登录
            </Button>
          )}
        </Space>
      </div>
    </Header>
  );
};

export default AppHeader;