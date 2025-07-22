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
  Space, 
  Popconfirm,
  Tag,
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
import { useAuth } from '../context/AuthContext';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const GroupManagement = () => {
  const { user: currentUser } = useAuth(); // 获取当前登录用户信息
  const [groups, setGroups] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('create'); // 'create' or 'edit'
  const [form] = Form.useForm();
  const [currentGroup, setCurrentGroup] = useState(null);
  const [customsCodes, setCustomsCodes] = useState([]);
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
      message.error('获取海关编码列表失败');
    }
  };

  useEffect(() => {
    fetchGroups();
    fetchUsers();
    fetchCustomsCodes();
  }, []);

  // 渲染海关编码权限的函数
  const renderCustomsCodesPermission = (codes) => {
    // 检查当前登录用户是否为管理员
    const isCurrentUserAdmin = currentUser?.is_admin || currentUser?.role_id === 'admin';
    
    if (!codes || codes.length === 0) {
      if (isCurrentUserAdmin) {
        // 管理员看到的是"无限制"
        return <span style={{ color: '#999' }}>无限制</span>;
      } else {
        // 普通用户看到的是"无"
        return <span style={{ color: '#999' }}>无</span>;
      }
    }
    
    // 有具体的海关编码权限
    return (
      <div>
        {codes.slice(0, 3).map(code => (
          <Tag key={code} color="green" style={{ marginBottom: 4 }}>
            {code}
          </Tag>
        ))}
        {codes.length > 3 && (
          <Tag color="default">+{codes.length - 3}个</Tag>
        )}
      </div>
    );
  };

  // 表格列定义
  const columns = [
    {
      title: '用户组名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text) => <strong>{text}</strong>
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true,
      render: (text) => text || <span style={{ color: '#999' }}>无描述</span>
    },
    {
      title: '允许访问的海关编码',
      dataIndex: 'allowed_customs_codes',
      key: 'allowed_customs_codes',
      width: 250,
      render: (codes) => renderCustomsCodesPermission(codes)
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

  // 显示创建用户组模态框
  const showCreateModal = () => {
    setModalType('create');
    setCurrentGroup(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 显示编辑用户组模态框
  const handleEdit = (group) => {
    setModalType('edit');
    setCurrentGroup(group);
    form.setFieldsValue({
      name: group.name,
      description: group.description,
      allowed_customs_codes: group.allowed_customs_codes || []
    });
    setModalVisible(true);
  };

  // 关闭模态框
  const handleCancel = () => {
    setModalVisible(false);
    form.resetFields();
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

  // 提交表单（创建或编辑用户组）
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

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
      console.error(`${modalType === 'create' ? '创建' : '更新'}用户组失败:`, error);
      message.error(`${modalType === 'create' ? '创建' : '更新'}用户组失败，请重试`);
    } finally {
      setLoading(false);
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
    <div>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>
          用户组列表
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={showCreateModal}
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
        scroll={{ x: 1000 }}
      />

      {/* 创建/编辑用户组模态框 */}
      <Modal
        title={modalType === 'create' ? '创建用户组' : '编辑用户组'}
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
            label="允许访问的海关编码"
            name="allowed_customs_codes"
            extra="不选择表示可以访问所有海关编码，此权限与用户直接权限叠加"
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