import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tag,
  Space,
  Card,
  Descriptions
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { roleAPI } from '../utils/api';

const { Option } = Select;
const { TextArea } = Input;

const RoleManagement = () => {
  const [roles, setRoles] = useState([]);
  const [availablePermissions, setAvailablePermissions] = useState({});
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchRoles();
    fetchAvailablePermissions();
  }, []);

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const response = await roleAPI.getRoles();
      setRoles(response);
    } catch (error) {
      message.error('获取角色列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailablePermissions = async () => {
    try {
      const response = await roleAPI.getAvailablePermissions();
      setAvailablePermissions(response);
    } catch (error) {
      message.error('获取可用权限失败');
    }
  };

  const handleCreate = () => {
    setEditingRole(null);
    setModalVisible(true);
    form.resetFields();
  };

  const handleEdit = (role) => {
    setEditingRole(role);
    setModalVisible(true);
    form.setFieldsValue({
      name: role.name,
      description: role.description,
      permissions: role.permissions
    });
  };

  const handleView = (role) => {
    setSelectedRole(role);
    setDetailModalVisible(true);
  };

  const handleDelete = async (roleId) => {
    try {
      await roleAPI.deleteRole(roleId);
      message.success('角色删除成功');
      fetchRoles();
    } catch (error) {
      message.error(error.response?.data?.detail || '删除角色失败');
    }
  };

  const handleSubmit = async (values) => {
    try {
      if (editingRole) {
        await roleAPI.updateRole(editingRole.id, values);
        message.success('角色更新成功');
      } else {
        await roleAPI.createRole(values);
        message.success('角色创建成功');
      }
      setModalVisible(false);
      fetchRoles();
    } catch (error) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <span>{text}</span>
          {record.is_system && <Tag color="blue">系统角色</Tag>}
        </Space>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '权限数量',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions) => (
        <Tag color="green">{permissions?.length || 0} 个权限</Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString()
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          >
            查看
          </Button>
          {!record.is_system && (
            <>
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
              <Popconfirm
                title="确定要删除这个角色吗？"
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
            </>
          )}
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          创建角色
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={roles}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`
        }}
      />

      {/* 创建/编辑角色模态框 */}
      <Modal
        title={editingRole ? '编辑角色' : '创建角色'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="请输入角色名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="角色描述"
          >
            <TextArea
              rows={3}
              placeholder="请输入角色描述"
            />
          </Form.Item>

          <Form.Item
            name="permissions"
            label="角色权限"
            rules={[{ required: true, message: '请选择角色权限' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择角色权限"
              style={{ width: '100%' }}
            >
              {Object.entries(availablePermissions).map(([key, value]) => (
                <Option key={key} value={key}>
                  {value}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingRole ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 角色详情模态框 */}
      <Modal
        title="角色详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        {selectedRole && (
          <Card>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="角色名称">
                <Space>
                  {selectedRole.name}
                  {selectedRole.is_system && <Tag color="blue">系统角色</Tag>}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="角色描述">
                {selectedRole.description || '无描述'}
              </Descriptions.Item>
              <Descriptions.Item label="角色权限">
                <div>
                  {selectedRole.permissions?.map(permission => (
                    <Tag key={permission} color="green" style={{ margin: '2px' }}>
                      {availablePermissions[permission] || permission}
                    </Tag>
                  ))}
                </div>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {new Date(selectedRole.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {new Date(selectedRole.updated_at).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </Modal>
    </div>
  );
};

export default RoleManagement;