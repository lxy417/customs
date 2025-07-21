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
  Card, 
  Spin, 
  Space, 
  Popconfirm,
  Tag,
  Divider,
  Transfer
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
import { groupAPI, userAPI, dataAPI } from '../utils/api';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const GroupManagement = () => {
  const [groups, setGroups] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('create'); // 'create' or 'edit'
  const [form] = Form.useForm();
  const [currentGroup, setCurrentGroup] = useState(null);
  const [customsCodes, setCustomsCodes] = useState([]);
  const [availablePermissions, setAvailablePermissions] = useState([]);
  const [userModalVisible, setUserModalVisible] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [transferData, setTransferData] = useState([]);
  const [targetKeys, setTargetKeys] = useState([]);

  // 获取用户组列表
  const fetchGroups = async () => {
    try {
      setLoading(true);
      const response = await groupAPI.getGroups();
      setGroups(response);
    } catch (error) {
      console.error('获取用户组列表失败:', error);
      message.error('获取用户组列表失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      const response = await userAPI.getUsers();
      setUsers(response);
    } catch (error) {
      console.error('获取用户列表失败:', error);
    }
  };

  // 获取海关编码列表
  const fetchCustomsCodes = async () => {
    try {
      const response = await dataAPI.getCustomsCodes();
      setCustomsCodes(response);
    } catch (error) {
      console.error('获取海关编码失败:', error);
    }
  };

  // 获取可用权限列表
  const fetchAvailablePermissions = async () => {
    try {
      const response = await groupAPI.getAvailablePermissions();
      setAvailablePermissions(response);
    } catch (error) {
      console.error('获取权限列表失败:', error);
    }
  };

  useEffect(() => {
    fetchGroups();
    fetchUsers();
    fetchCustomsCodes();
    fetchAvailablePermissions();
  }, []);

  // 权限名称映射
  const permissionNames = {
    'data_view': '查看数据',
    'data_export': '导出数据',
    'data_create': '创建数据',
    'data_update': '更新数据',
    'data_delete': '删除数据',
    'data_import': '导入数据',
    'user_manage': '用户管理',
    'group_manage': '用户组管理',
    'ai_search': 'AI搜索'
  };

  // 表格列定义
  const columns = [
    {
      title: '用户组名称',
      dataIndex: 'name',
      key: 'name',
      render: (text) => <strong>{text}</strong>
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '权限',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions) => (
        <div>
          {permissions?.slice(0, 3).map(permission => (
            <Tag key={permission} color="blue" style={{ marginBottom: 4 }}>
              {permissionNames[permission] || permission}
            </Tag>
          ))}
          {permissions?.length > 3 && (
            <Tag color="default">+{permissions.length - 3}个</Tag>
          )}
        </div>
      )
    },
    {
      title: '海关编码',
      dataIndex: 'allowed_customs_codes',
      key: 'allowed_customs_codes',
      render: (codes) => (
        <div>
          {codes?.slice(0, 2).map(code => (
            <Tag key={code} color="green" style={{ marginBottom: 4 }}>
              {code}
            </Tag>
          ))}
          {codes?.length > 2 && (
            <Tag color="default">+{codes.length - 2}个</Tag>
          )}
          {(!codes || codes.length === 0) && <span style={{ color: '#999' }}>无限制</span>}
        </div>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            icon={<UserOutlined />}
            onClick={() => handleManageUsers(record)}
          >
            管理用户
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个用户组吗？"
            description="删除后无法恢复，且会影响组内用户的权限。"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 处理创建用户组
  const handleCreate = () => {
    setModalType('create');
    setCurrentGroup(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 处理编辑用户组
  const handleEdit = (group) => {
    setModalType('edit');
    setCurrentGroup(group);
    form.setFieldsValue({
      name: group.name,
      description: group.description,
      permissions: group.permissions || [],
      allowed_customs_codes: group.allowed_customs_codes || []
    });
    setModalVisible(true);
  };

  // 处理删除用户组
  const handleDelete = async (groupId) => {
    try {
      await groupAPI.deleteGroup(groupId);
      message.success('用户组删除成功');
      fetchGroups();
    } catch (error) {
      console.error('删除用户组失败:', error);
      message.error('删除用户组失败，请重试');
    }
  };

  // 处理管理用户
  const handleManageUsers = async (group) => {
    try {
      setSelectedGroup(group);
      
      // 获取用户组详情（包含用户列表）
      const groupDetail = await groupAPI.getGroup(group.id);
      const usersInGroup = groupDetail.users || [];
      
      // 准备穿梭框数据
      const transferDataSource = users.map(user => ({
        key: user.username,
        title: user.username,
        description: user.is_admin ? '管理员' : '普通用户'
      }));
      
      const targetUserKeys = usersInGroup.map(user => user.username);
      
      setTransferData(transferDataSource);
      setTargetKeys(targetUserKeys);
      setUserModalVisible(true);
    } catch (error) {
      console.error('获取用户组详情失败:', error);
      message.error('获取用户组详情失败');
    }
  };

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (modalType === 'create') {
        await groupAPI.createGroup(values);
        message.success('用户组创建成功');
      } else {
        await groupAPI.updateGroup(currentGroup.id, values);
        message.success('用户组更新成功');
      }
      
      setModalVisible(false);
      fetchGroups();
    } catch (error) {
      console.error('操作失败:', error);
      message.error('操作失败，请重试');
    }
  };

  // 处理用户组成员变更
  const handleUserTransferChange = (newTargetKeys) => {
    setTargetKeys(newTargetKeys);
  };

  // 保存用户组成员变更
  const handleSaveUserChanges = async () => {
    try {
      // 获取当前用户组的用户列表
      const groupDetail = await groupAPI.getGroup(selectedGroup.id);
      const currentUsers = groupDetail.users || [];
      const currentUsernames = currentUsers.map(user => user.username);
      
      // 计算需要添加和移除的用户
      const usersToAdd = targetKeys.filter(username => !currentUsernames.includes(username));
      const usersToRemove = currentUsernames.filter(username => !targetKeys.includes(username));
      
      // 执行添加操作
      for (const username of usersToAdd) {
        await groupAPI.addUserToGroup(selectedGroup.id, username);
      }
      
      // 执行移除操作
      for (const username of usersToRemove) {
        await groupAPI.removeUserFromGroup(selectedGroup.id, username);
      }
      
      message.success('用户组成员更新成功');
      setUserModalVisible(false);
      fetchGroups();
    } catch (error) {
      console.error('更新用户组成员失败:', error);
      message.error('更新用户组成员失败，请重试');
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={3} style={{ margin: 0 }}>
            <TeamOutlined style={{ marginRight: '8px' }} />
            用户组管理
          </Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            创建用户组
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={groups}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个用户组`
          }}
        />
      </Card>

      {/* 创建/编辑用户组模态框 */}
      <Modal
        title={modalType === 'create' ? '创建用户组' : '编辑用户组'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setModalVisible(false)}>
            <CloseOutlined /> 取消
          </Button>,
          <Button key="submit" type="primary" onClick={handleSubmit}>
            <SaveOutlined /> {modalType === 'create' ? '创建' : '更新'}
          </Button>
        ]}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            permissions: [],
            allowed_customs_codes: []
          }}
        >
          <Form.Item
            label="用户组名称"
            name="name"
            rules={[
              { required: true, message: '请输入用户组名称' },
              { min: 2, max: 50, message: '用户组名称长度应在2-50个字符之间' }
            ]}
          >
            <Input placeholder="请输入用户组名称" />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <TextArea 
              placeholder="请输入用户组描述（可选）" 
              rows={3}
              maxLength={200}
              showCount
            />
          </Form.Item>

          <Form.Item
            label="权限"
            name="permissions"
          >
            <Select
              mode="multiple"
              placeholder="请选择权限"
              style={{ width: '100%' }}
            >
              {availablePermissions.map(permission => (
                <Option key={permission} value={permission}>
                  {permissionNames[permission] || permission}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="允许访问的海关编码"
            name="allowed_customs_codes"
            extra="不选择表示可以访问所有海关编码"
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

      {/* 管理用户组成员模态框 */}
      <Modal
        title={`管理用户组成员 - ${selectedGroup?.name}`}
        open={userModalVisible}
        onCancel={() => setUserModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setUserModalVisible(false)}>
            取消
          </Button>,
          <Button key="submit" type="primary" onClick={handleSaveUserChanges}>
            保存更改
          </Button>
        ]}
        width={700}
      >
        <div style={{ marginBottom: '16px' }}>
          <p>左侧为所有用户，右侧为当前用户组成员。拖拽或点击箭头来调整成员。</p>
        </div>
        <Transfer
          dataSource={transferData}
          targetKeys={targetKeys}
          onChange={handleUserTransferChange}
          render={item => item.title}
          titles={['所有用户', '用户组成员']}
          listStyle={{
            width: 300,
            height: 400,
          }}
          showSearch
          filterOption={(inputValue, option) =>
            option.title.indexOf(inputValue) > -1
          }
        />
      </Modal>
    </div>
  );
};

export default GroupManagement;