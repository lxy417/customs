import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Checkbox, Select, message, Typography, Card, Spin, Space, Popconfirm } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SaveOutlined, CloseOutlined } from '@ant-design/icons';
import { userAPI, dataAPI } from '../utils/api';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
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
    fetchCustomsCodes();
  }, []);

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
      allowed_customs_codes: user.allowed_customs_codes
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
          allowed_customs_codes: values.allowed_customs_codes || []
        });
        message.success('用户创建成功');
      } else {
        // 编辑现有用户
        const updateData = {
          is_admin: values.is_admin || false,
          allowed_customs_codes: values.allowed_customs_codes || []
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
      width: 150
    },
    {
      title: '管理员权限',
      dataIndex: 'is_admin',
      key: 'is_admin',
      width: 120,
      render: (isAdmin) => (
        <Checkbox checked={isAdmin} disabled />
      )
    },
    {
      title: '允许访问的海关编码',
      dataIndex: 'allowed_customs_codes',
      key: 'allowed_customs_codes',
      render: (codes) => (
        <TextArea
          value={codes.join(', ')}
          rows={2}
          readOnly
          style={{ width: '100%', resize: 'none' }}
        />
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="primary"
            icon={<EditOutlined />}
            size="small"
            onClick={() => showEditModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此用户吗?"
            onConfirm={() => handleDelete(record.username)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              danger
              icon={<DeleteOutlined />}
              size="small"
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
    <div className="user-management-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={2}>用户管理</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={showCreateModal}
        >
          添加用户
        </Button>
      </div>

      <Card>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={users.map(user => ({ ...user, key: user.username }))}
            pagination={{ pageSize: 10 }}
            rowKey="username"
            bordered
          />
        </Spin>
      </Card>

      {/* 创建/编辑用户模态框 */}
      <Modal
        title={modalType === 'create' ? '创建新用户' : '编辑用户'}
        open={modalVisible}
        onCancel={handleCancel}
        footer={null}
        destroyOnClose
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ is_admin: false, allowed_customs_codes: [] }}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { max: 50, message: '用户名不能超过50个字符' }
            ]}
          >
            <Input
              placeholder="请输入用户名"
              disabled={modalType === 'edit'} // 编辑时用户名不可修改
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: modalType === 'create', message: '请输入密码' },
              { min: 6, message: '密码长度不能少于6个字符' },
              { max: 32, message: '密码长度不能超过32个字符' }
            ]}
            tooltip={modalType === 'edit' ? '不修改密码请留空' : ''}
          >
            <Input.Password placeholder={modalType === 'create' ? '请输入密码' : '请输入新密码'} />
          </Form.Item>

          <Form.Item
            name="is_admin"
            label="管理员权限"
          >
            <Checkbox>是否授予管理员权限</Checkbox>
          </Form.Item>

          <Form.Item
            name="allowed_customs_codes"
            label="允许访问的海关编码"
            tooltip="选择用户可以访问的海关编码，不选择则可以访问所有编码"
          >
            <Select
              mode="multiple"
              placeholder="选择海关编码"
              style={{ width: '100%', maxHeight: 200, overflow: 'auto' }}
              showSearch
              filterOption={(input, option) =>
                (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
              }
            >
              {customsCodes.map(code => (
                <Option key={code} value={code}>{code}</Option>
              ))}
            </Select>
          </Form.Item>

          <div style={{ textAlign: 'right', marginTop: 24 }}>
            <Space size="middle">
              <Button icon={<CloseOutlined />} onClick={handleCancel}>
                取消
              </Button>
              <Button type="primary" icon={<SaveOutlined />} onClick={handleSubmit} loading={loading}>
                {modalType === 'create' ? '创建' : '保存'}
              </Button>
            </Space>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagement;