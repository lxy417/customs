import React, { useState } from 'react';
import { 
  Typography, 
  Card, 
  Tabs
} from 'antd';
import { 
  UserOutlined,
  TeamOutlined,
  SafetyOutlined
} from '@ant-design/icons';
import { useAuth } from '../context/AuthContext';
import { usePermissions, PERMISSIONS } from '../utils/permissions';
import UserManagement from '../components/UserManagement';
import GroupManagement from '../components/GroupManagement';
import RoleManagement from '../components/RoleManagement';

const { Title } = Typography;
const { TabPane } = Tabs;

const UserManagementPage = () => {
  const { user: currentUser } = useAuth();
  const { hasPermission } = usePermissions(currentUser);
  const [activeTab, setActiveTab] = useState(() => {
    // 根据权限设置默认激活的标签页
    if (hasPermission(PERMISSIONS.USER_MANAGE)) return 'users';
    if (hasPermission(PERMISSIONS.ROLE_MANAGE)) return 'roles';
    if (hasPermission(PERMISSIONS.GROUP_MANAGE)) return 'groups';
    return 'users'; // 默认值
  });

  // 处理标签页切换
  const handleTabChange = (key) => {
    setActiveTab(key);
  };

  // 获取可用的标签页
  const getAvailableTabs = () => {
    const tabs = [];
    
    if (hasPermission(PERMISSIONS.USER_MANAGE)) {
      tabs.push({
        key: 'users',
        tab: (
          <span>
            <UserOutlined />
            用户管理
          </span>
        ),
        component: <UserManagement />
      });
    }
    
    if (hasPermission(PERMISSIONS.ROLE_MANAGE)) {
      tabs.push({
        key: 'roles',
        tab: (
          <span>
            <SafetyOutlined />
            角色管理
          </span>
        ),
        component: <RoleManagement />
      });
    }
    
    if (hasPermission(PERMISSIONS.GROUP_MANAGE)) {
      tabs.push({
        key: 'groups',
        tab: (
          <span>
            <TeamOutlined />
            用户组管理
          </span>
        ),
        component: <GroupManagement />
      });
    }
    
    return tabs;
  };

  const availableTabs = getAvailableTabs();

  // 如果用户没有任何管理权限，显示提示信息
  if (availableTabs.length === 0) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Title level={4}>您没有访问此页面的权限</Title>
            <p>请联系管理员获取相应的管理权限。</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={handleTabChange}
          type="card"
        >
          {availableTabs.map(tab => (
            <TabPane tab={tab.tab} key={tab.key}>
              {/* 只有当前激活的标签页才渲染组件，实现按需加载 */}
              {activeTab === tab.key && tab.component}
            </TabPane>
          ))}
        </Tabs>
      </Card>
    </div>
  );
};

export default UserManagementPage;