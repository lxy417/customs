import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  message, 
  Typography, 
  Space, 
  Popconfirm,
  Tag
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SaveOutlined, 
  CloseOutlined
} from '@ant-design/icons';
import { userAPI, dataAPI, groupAPI, roleAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { usePermissions, PERMISSIONS } from '../utils/permissions';

const { Title } = Typography;
const { Option } = Select;

const UserManagement = () => {
  const { user: currentUser } = useAuth();
  const { hasPermission } = usePermissions(currentUser);
  const [users, setUsers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [roles, setRoles] = useState([]);
  const [availablePermissions, setAvailablePermissions] = useState({});
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('create');
  const [form] = Form.useForm();
  const [currentEditUser, setCurrentEditUser] = useState(null);
  const [customsCodes, setCustomsCodes] = useState([]);

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await userAPI.getUsers();
      setUsers(response);
    } catch (error) {
      console.error('获取用户列表失败:', error);
      message.error('获取用户列表失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 获取用户组列表
  const fetchGroups = async () => {
    try {
      const response = await groupAPI.getGroups();
      setGroups(response);
    } catch (error) {
      console.error('获取用户组列表失败:', error);
    }
  };

  // 获取角色列表
  const fetchRoles = async () => {
    try {
      const response = await roleAPI.getRoles();
      setRoles(response);
    } catch (error) {
      console.error('获取角色列表失败:', error);
    }
  };

  // 获取可用权限列表
  const fetchAvailablePermissions = async () => {
    try {
      const response = await roleAPI.getAvailablePermissions();
      setAvailablePermissions(response);
    } catch (error) {
      console.error('获取可用权限失败:', error);
    }
  };

  // 获取海关编码列表
  const fetchCustomsCodes = async () => {
    try {
      const response = await dataAPI.getCustomsCodes();
      setCustomsCodes(response);
    } catch (error) {
      console.error('获取海关编码列表失败:', error);
      message.error('获取海关编码列表失败');
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchUsers();
    fetchGroups();
    fetchRoles();
    fetchAvailablePermissions();
    fetchCustomsCodes();
  }, []);

  // 根据用户组ID获取用户组名称
  const getGroupNames = (groupIds) => {
    if (!groupIds || groupIds.length === 0) return [];
    return groupIds.map(id => {
      const group = groups.find(g => g.id === id);
      return group ? group.name : id;
    });
  };

  // 根据角色ID获取角色名称
  const getRoleName = (roleId) => {
    const role = roles.find(r => r.id === roleId);
    return role ? role.name : roleId;
  };

  // 渲染海关编码权限的函数
  const renderCustomsCodesPermission = (codes, userRecord) => {
    const isTargetUserAdmin = userRecord?.is_admin || userRecord?.role_id === 'admin';
    
    if (isTargetUserAdmin) {
      return <Tag color="gold">无限制</Tag>;
    }
    
    if (!codes || codes.length === 0) {
      return <span style={{ color: '#999' }}>无</span>;
    }
    
    return (
      <div>
        {codes.slice(0, 3).map(code => (
          <Tag key={code} color="purple" style={{ marginBottom: 4 }}>
            {code}
          </Tag>
        ))}
        {codes.length > 3 && (
          <Tag color="default">+{codes.length - 3}个</Tag>
        )}
      </div>
    );
  };

  // 显示创建用户模态框
  const showCreateModal = () => {
    setModalType('create');
    setCurrentEditUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 显示编辑用户模态框
  const showEditModal = (user) => {
    setModalType('edit');
    setCurrentEditUser(user);
    form.setFieldsValue({
      username: user.username,
      password: '',
      role_id: user.role_id,
      additional_permissions: user.additional_permissions || [],
      allowed_customs_codes: user.allowed_customs_codes,
      group_ids: user.group_ids || []
    });
    setModalVisible(true);
  };

  // 关闭模态框
  const handleCancel = () => {
    setModalVisible(false);
    form.resetFields();
  };

  // 删除用户
  const handleDelete = async (username) => {
    try {
      setLoading(true);
      await userAPI.deleteUser(username);
      message.success('用户删除成功');
      fetchUsers();
    } catch (error) {
      console.error('删除用户失败:', error);
      message.error('删除用户失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 提交表单（创建或编辑用户）
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      if (modalType === 'create') {
        await userAPI.createUser({
          username: values.username,
          password: values.password,
          role_id: values.role_id,
          additional_permissions: values.additional_permissions || [],
          allowed_customs_codes: values.allowed_customs_codes || [],
          group_ids: values.group_ids || []
        });
        message.success('用户创建成功');
      } else {
        const updateData = {
          role_id: values.role_id,
          additional_permissions: values.additional_permissions || [],
          allowed_customs_codes: values.allowed_customs_codes || [],
          group_ids: values.group_ids || []
        };
        if (values.password) {
          updateData.password = values.password;
        }
        await userAPI.updateUser(currentEditUser.username, updateData);
        message.success('用户更新成功');
      }

      setModalVisible(false);
      fetchUsers();
    } catch (error) {
      console.error(`${modalType === 'create' ? '创建' : '更新'}用户失败:`, error);
      message.error(error.response?.data?.detail || `${modalType === 'create' ? '创建' : '更新'}用户失败，请重试`);
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      render: (text) => <strong>{text}</strong>
    },
    {
      title: '角色',
      dataIndex: 'role_id',
      key: 'role_id',
      width: 100,
      render: (roleId) => {
        const roleName = getRoleName(roleId);
        const isAdmin = roleId === 'admin';
        return (
          <Tag color={isAdmin ? 'red' : 'blue'}>
            {roleName}
          </Tag>
        );
      }
    },
    {
      title: '额外权限',
      dataIndex: 'additional_permissions',
      key: 'additional_permissions',
      width: 200,
      render: (permissions) => (
        <div>
          {permissions?.slice(0, 2).map(permission => (
            <Tag key={permission} color="orange" style={{ marginBottom: 4 }}>
              {availablePermissions[permission] || permission}
            </Tag>
          ))}
          {permissions?.length > 2 && (
            <Tag color="default">+{permissions.length - 2}个</Tag>
          )}
          {(!permissions || permissions.length === 0) && (
            <span style={{ color: '#999' }}>无</span>
          )}
        </div>
      )
    },
    {
      title: '所属用户组',
      dataIndex: 'group_ids',
      key: 'group_ids',
      width: 200,
      render: (groupIds) => {
        const groupNames = getGroupNames(groupIds);
        return (
          <div>
            {groupNames.map(name => (
              <Tag key={name} color="green" style={{ marginBottom: 4 }}>
                {name}
              </Tag>
            ))}
            {(!groupNames || groupNames.length === 0) && (
              <span style={{ color: '#999' }}>未分配用户组</span>
            )}
          </div>
        );
      }
    },
    {
      title: '允许访问的海关编码',
      dataIndex: 'allowed_customs_codes',
      key: 'allowed_customs_codes',
      width: 250,
      render: (codes, record) => renderCustomsCodesPermission(codes, record)
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date) => new Date(date).toLocaleString()
    },
    // 只有拥有用户管理权限的用户才能看到操作列
    ...(hasPermission(PERMISSIONS.USER_MANAGE) ? [{
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => showEditModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此用户吗?"
            description="删除后无法恢复，请谨慎操作。"
            onConfirm={() => handleDelete(record.username)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              disabled={record.username === 'admin'}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }] : [])
  ];

  return (
    <div>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>
          用户列表
        </Title>
        {hasPermission(PERMISSIONS.USER_MANAGE) && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={showCreateModal}
          >
            创建用户
          </Button>
        )}
      </div>

      <Table
        columns={columns}
        dataSource={users}
        rowKey="username"
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 个用户`
        }}
        scroll={{ x: 1400 }}
      />

      {/* 创建/编辑用户模态框 */}
      {hasPermission(PERMISSIONS.USER_MANAGE) && (
        <Modal
          title={modalType === 'create' ? '创建用户' : '编辑用户'}
          open={modalVisible}
          onCancel={handleCancel}
          footer={[
            <Button key="cancel" onClick={handleCancel}>
              <CloseOutlined /> 取消
            </Button>,
            <Button key="submit" type="primary" onClick={handleSubmit} loading={loading}>
              <SaveOutlined /> {modalType === 'create' ? '创建' : '更新'}
            </Button>
          ]}
          width={700}
        >
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              additional_permissions: [],
              allowed_customs_codes: [],
              group_ids: []
            }}
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, max: 20, message: '用户名长度应在3-20个字符之间' },
                { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
              ]}
            >
              <Input 
                placeholder="请输入用户名" 
                disabled={modalType === 'edit'}
              />
            </Form.Item>

            <Form.Item
              label="密码"
              name="password"
              rules={modalType === 'create' ? [
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码长度至少6个字符' }
              ] : [
                { min: 6, message: '密码长度至少6个字符' }
              ]}
              extra={modalType === 'edit' ? '留空表示不修改密码' : ''}
            >
              <Input.Password placeholder={modalType === 'create' ? '请输入密码' : '留空表示不修改密码'} />
            </Form.Item>

            <Form.Item
              label="用户角色"
              name="role_id"
              rules={[{ required: true, message: '请选择用户角色' }]}
              extra="用户将获得所选角色的基础权限"
            >
              <Select placeholder="请选择用户角色">
                {roles.map(role => (
                  <Option key={role.id} value={role.id}>
                    <Space>
                      {role.name}
                      {role.is_system && <Tag size="small" color="blue">系统角色</Tag>}
                    </Space>
                    {role.description && (
                      <div style={{ color: '#999', fontSize: '12px' }}>
                        {role.description}
                      </div>
                    )}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="额外权限"
              name="additional_permissions"
              extra="这些权限将与角色权限合并，为用户提供额外的功能访问权限"
            >
              <Select
                mode="multiple"
                placeholder="请选择额外权限（可选）"
                style={{ width: '100%' }}
              >
                {Object.entries(availablePermissions).map(([key, value]) => (
                  <Option key={key} value={key}>
                    {value}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="所属用户组"
              name="group_ids"
              extra="用户将继承所属用户组的海关编码访问权限"
            >
              <Select
                mode="multiple"
                placeholder="请选择用户组（可选）"
                style={{ width: '100%' }}
              >
                {groups.map(group => (
                  <Option key={group.id} value={group.id}>
                    {group.name}
                    {group.description && (
                      <span style={{ color: '#999', marginLeft: 8 }}>
                        - {group.description}
                      </span>
                    )}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="允许访问的海关编码"
              name="allowed_customs_codes"
              extra="不选择表示可以访问所有海关编码，此权限与用户组权限叠加"
            >
              <Select
                mode="multiple"
                placeholder="请选择海关编码（可选）"
                style={{ width: '100%' }}
                showSearch
                filterOption={(input, option) =>
                  option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                }
              >
                {customsCodes.map(code => (
                  <Option key={code} value={code}>
                    {code}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Form>
        </Modal>
      )}
    </div>
  );
};

export default UserManagement;