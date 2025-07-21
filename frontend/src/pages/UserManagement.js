import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Checkbox, 
  Select, 
  message, 
  Typography, 
  Card, 
  Spin, 
  Space, 
  Popconfirm,
  Tabs,
  Tag,
  Divider
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SaveOutlined, 
  CloseOutlined,
  UserOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { userAPI, dataAPI, groupAPI } from '../utils/api';
import GroupManagement from '../components/GroupManagement';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('create'); // 'create' or 'edit'
  const [form] = Form.useForm();
  const [currentUser, setCurrentUser] = useState(null);
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

  // 显示创建用户模态框
  const showCreateModal = () => {
    setModalType('create');
    setCurrentUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 显示编辑用户模态框
  const showEditModal = (user) => {
    setModalType('edit');
    setCurrentUser(user);
    form.setFieldsValue({
      username: user.username,
      password: '', // 不显示现有密码
      is_admin: user.is_admin,
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

  // 提交表单（创建或编辑用户）
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      if (modalType === 'create') {
        // 创建新用户
        await userAPI.createUser({
          username: values.username,
          password: values.password,
          is_admin: values.is_admin || false,
          allowed_customs_codes: values.allowed_customs_codes || [],
          group_ids: values.group_ids || []
        });
        message.success('用户创建成功');
      } else {
        // 编辑现有用户
        const updateData = {
          is_admin: values.is_admin || false,
          allowed_customs_codes: values.allowed_customs_codes || [],
          group_ids: values.group_ids || []
        };
        // 只有在提供了新密码时才更新密码
        if (values.password) {
          updateData.password = values.password;
        }
        await userAPI.updateUser(currentUser.username, updateData);
        message.success('用户更新成功');
      }

      setModalVisible(false);
      fetchUsers(); // 刷新用户列表
    } catch (error) {
      console.error(`${modalType === 'create' ? '创建' : '更新'}用户失败:`, error);
      message.error(`${modalType === 'create' ? '创建' : '更新'}用户失败，请重试`);
    } finally {
      setLoading(false);
    }
  };

  // 删除用户
  const handleDelete = async (username) => {
    try {
      setLoading(true);
      await userAPI.deleteUser(username);
      message.success('用户删除成功');
      fetchUsers(); // 刷新用户列表
    } catch (error) {
      console.error('删除用户失败:', error);
      message.error('删除用户失败，请重试');
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
      title: '管理员权限',
      dataIndex: 'is_admin',
      key: 'is_admin',
      width: 100,
      render: (isAdmin) => (
        <Tag color={isAdmin ? 'red' : 'default'}>
          {isAdmin ? '管理员' : '普通用户'}
        </Tag>
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
              <Tag key={name} color="blue" style={{ marginBottom: 4 }}>
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
      render: (codes) => (
        <div>
          {codes?.slice(0, 3).map(code => (
            <Tag key={code} color="green" style={{ marginBottom: 4 }}>
              {code}
            </Tag>
          ))}
          {codes?.length > 3 && (
            <Tag color="default">+{codes.length - 3}个</Tag>
          )}
          {(!codes || codes.length === 0) && (
            <span style={{ color: '#999' }}>无限制</span>
          )}
        </div>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date) => new Date(date).toLocaleString()
    },
    {
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
              disabled={record.username === 'admin'} // 禁止删除管理员
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Tabs defaultActiveKey="users" type="card">
          <TabPane 
            tab={
              <span>
                <UserOutlined />
                用户管理
              </span>
            } 
            key="users"
          >
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Title level={4} style={{ margin: 0 }}>
                用户列表
              </Title>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={showCreateModal}
              >
                创建用户
              </Button>
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
              scroll={{ x: 1200 }}
            />
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <TeamOutlined />
                用户组管理
              </span>
            } 
            key="groups"
          >
            <GroupManagement />
          </TabPane>
        </Tabs>
      </Card>

      {/* 创建/编辑用户模态框 */}
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
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            is_admin: false,
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
              disabled={modalType === 'edit'} // 编辑时不允许修改用户名
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
            label="管理员权限"
            name="is_admin"
            valuePropName="checked"
          >
            <Checkbox>设为管理员</Checkbox>
          </Form.Item>

          <Form.Item
            label="所属用户组"
            name="group_ids"
            extra="用户将继承所属用户组的权限"
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
    </div>
  );
};

export default UserManagement;