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
  Descriptions,
  Typography,
  InputNumber,
  Divider,
  Tooltip
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, SettingOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { roleAPI, configAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { usePermissions, PERMISSIONS } from '../utils/permissions';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const RoleManagement = () => {
  const { user } = useAuth();
  const { hasPermission } = usePermissions(user);
  const [roles, setRoles] = useState([]);
  const [availablePermissions, setAvailablePermissions] = useState({});
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
  const [roleConfigs, setRoleConfigs] = useState([]);
  const [configTypes, setConfigTypes] = useState({}); // 新增：配置类型元数据
  const [form] = Form.useForm();
  const [configForm] = Form.useForm();

  // 移除硬编码的CONFIG_TYPES

  // 组件挂载时加载数据
  useEffect(() => {
    fetchRoles();
    fetchAvailablePermissions();
    fetchConfigTypes(); // 新增：获取配置类型
  }, []);

  // 新增：获取配置类型元数据
  const fetchConfigTypes = async () => {
    try {
      const response = await configAPI.getConfigTypes();
      setConfigTypes(response);
    } catch (error) {
      console.error('获取配置类型失败:', error);
      message.error('获取配置类型失败');
    }
  };

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

  // 获取角色配置
  const fetchRoleConfigs = async (roleId) => {
    try {
      const response = await configAPI.getRoleConfigs(roleId);
      // 修复：直接使用返回的数组，而不是 response.configs
      setRoleConfigs(Array.isArray(response) ? response : []);
    } catch (error) {
      message.error('获取角色配置失败');
    }
  };

  // 保存角色配置
  const handleSaveRoleConfig = async (values) => {
    try {
      await configAPI.createRoleConfig({
        ...values,
        // 修复：确保 config_value 是字符串类型
        config_value: String(values.config_value),
        role_id: selectedRole.id
      });
      message.success('角色配置保存成功');
      fetchRoleConfigs(selectedRole.id);
      configForm.resetFields();
    } catch (error) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // 删除角色配置
  const handleDeleteRoleConfig = async (configKey) => {
    try {
      await configAPI.deleteRoleConfig(selectedRole.id, configKey);
      message.success('角色配置删除成功');
      fetchRoleConfigs(selectedRole.id);
    } catch (error) {
      message.error('删除失败');
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

  const handleConfig = (role) => {
    setSelectedRole(role);
    setConfigModalVisible(true);
    fetchRoleConfigs(role.id);
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
      width: 370,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          >
            查看
          </Button>
          {/* 配置管理按钮 - 需要配置管理权限 */}
          {hasPermission(PERMISSIONS.CONFIG_MANAGE) && (
            <Button
              type="link"
              icon={<SettingOutlined />}
              onClick={() => handleConfig(record)}
            >
              配置
            </Button>
          )}
          {/* 只有拥有角色管理权限的用户才能编辑和删除角色 */}
          {hasPermission(PERMISSIONS.ROLE_MANAGE) && !record.is_system && (
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
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>
          角色列表
        </Title>
        {/* 只有拥有角色管理权限的用户才能创建角色 */}
        {hasPermission(PERMISSIONS.ROLE_MANAGE) && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            创建角色
          </Button>
        )}
      </div>

      <Table
        columns={columns}
        dataSource={roles}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200, y: 600 }}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`
        }}
      />

      {/* 创建/编辑角色模态框 - 只有拥有角色管理权限的用户才能看到 */}
      {hasPermission(PERMISSIONS.ROLE_MANAGE) && (
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
      )}

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

      {/* 角色配置管理模态框 */}
      <Modal
        title={`角色配置管理 - ${selectedRole?.name}`}
        open={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setConfigModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedRole && (
          <div>
            {/* 添加新配置 */}
            {hasPermission(PERMISSIONS.CONFIG_MANAGE) && (
              <Card title="添加角色配置" style={{ marginBottom: 16 }}>
                <Form
                  form={configForm}
                  layout="inline"
                  onFinish={handleSaveRoleConfig}
                >
                  <Form.Item
                    name="config_key"
                    rules={[{ required: true, message: '请选择配置项' }]}
                  >
                    <Select placeholder="选择配置项" style={{ width: 200 }}>
                      {Object.entries(configTypes).map(([key, config]) => (
                        <Option key={key} value={key}>
                          {config.label}
                          <Tooltip title={config.description}>
                            <InfoCircleOutlined style={{ marginLeft: 8, color: '#999' }} />
                          </Tooltip>
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>

                  <Form.Item
                    name="config_value"
                    rules={[{ required: true, message: '请输入配置值' }]}
                  >
                    <InputNumber
                      placeholder="配置值"
                      min={(() => {
                        const configKey = configForm.getFieldValue('config_key');
                        return configKey && configTypes[configKey] ? configTypes[configKey].min : -1;
                      })()}
                      max={(() => {
                        const configKey = configForm.getFieldValue('config_key');
                        return configKey && configTypes[configKey] ? configTypes[configKey].max : undefined;
                      })()}
                      style={{ width: 120 }}
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button type="primary" htmlType="submit">
                      添加
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            )}

            {/* 现有配置列表 */}
            <Card title="当前角色配置">
              {roleConfigs.length > 0 ? (
                <Table
                  dataSource={roleConfigs}
                  rowKey={(record) => `${record.role_id}-${record.config_key}`}
                  pagination={false}
                  size="small"
                  scroll={{ x: 800, y: 300 }}
                  columns={[
                    {
                      title: '配置项',
                      dataIndex: 'config_key',
                      key: 'config_key',
                      render: (key) => configTypes[key]?.label || key
                    },
                    {
                      title: '配置值',
                      dataIndex: 'config_value',
                      key: 'config_value',
                      render: (value, record) => {
                        const configType = configTypes[record.config_key];
                        if (configType?.type === 'number' && value === '-1') {
                          return <span style={{ color: '#52c41a' }}>不限制</span>;
                        }
                        return value;
                      }
                    },
                    {
                      title: '描述',
                      dataIndex: 'config_key',
                      key: 'description',
                      render: (key) => configTypes[key]?.description || '-'
                    },
                    {
                      title: '更新时间',
                      dataIndex: 'updated_at',
                      key: 'updated_at',
                      render: (time) => time ? new Date(time).toLocaleString() : '-'
                    },
                    ...(hasPermission(PERMISSIONS.CONFIG_MANAGE) ? [{
                      title: '操作',
                      key: 'action',
                      render: (_, record) => (
                        <Popconfirm
                          title="确定要删除这个配置吗？"
                          onConfirm={() => handleDeleteRoleConfig(record.config_key)}
                          okText="确定"
                          cancelText="取消"
                        >
                          <Button
                            type="link"
                            danger
                            size="small"
                            icon={<DeleteOutlined />}
                          >
                            删除
                          </Button>
                        </Popconfirm>
                      )
                    }] : [])
                  ]}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                  暂无角色配置
                </div>
              )}
            </Card>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RoleManagement;