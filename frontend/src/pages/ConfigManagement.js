import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  message, 
  Space, 
  Popconfirm,
  Tabs,
  Switch,
  Tooltip
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  InfoCircleOutlined,
  ReloadOutlined 
} from '@ant-design/icons';
import { useAuth } from '../context/AuthContext';
import { usePermissions, PERMISSIONS } from '../utils/permissions';
import { configAPI, roleAPI } from '../utils/api';

const { TabPane } = Tabs;
const { Option } = Select;

const ConfigManagement = () => {
  const { user } = useAuth();
  const { hasPermission } = usePermissions(user);
  const [loading, setLoading] = useState(false);
  const [systemConfigs, setSystemConfigs] = useState([]);
  const [roleConfigs, setRoleConfigs] = useState([]);
  const [roles, setRoles] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [editingRoleConfig, setEditingRoleConfig] = useState(null);
  const [form] = Form.useForm();
  const [roleForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('system');

  const canManage = hasPermission(PERMISSIONS.CONFIG_MANAGE);
  const canView = hasPermission(PERMISSIONS.CONFIG_VIEW);

  // 配置类型定义
  const CONFIG_TYPES = {
    'export_limit': { label: '默认导出条数限制', type: 'number', min: -1, description: '用户默认可导出的数据条数，-1表示不限制' },
    'export_max_limit': { label: '最大导出条数限制', type: 'number', min: -1, description: '用户最多可导出的数据条数，-1表示不限制' },
    'import_batch_size': { label: '导入批次大小', type: 'number', min: 1, description: '数据导入时每批次处理的记录数' },
    'session_timeout': { label: '会话超时时间(分钟)', type: 'number', min: 1, description: '用户会话的超时时间' },
    'max_search_results': { label: '最大搜索结果数', type: 'number', min: 1, description: '搜索时返回的最大结果数量' }
  };

  useEffect(() => {
    if (canView) {
      fetchSystemConfigs();
      fetchRoleConfigs();
      fetchRoles();
    }
  }, [canView]);

  // 获取系统配置
  const fetchSystemConfigs = async () => {
    setLoading(true);
    try {
      const response = await configAPI.getSystemConfigs();
      // 直接使用返回的数组，不需要 response.configs
      setSystemConfigs(Array.isArray(response) ? response : []);
    } catch (error) {
      message.error('获取系统配置失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取角色配置
  // 获取角色配置
  const fetchRoleConfigs = async () => {
    try {
      const response = await configAPI.getAllRoleConfigs(); // 改为获取所有角色配置
      // 直接使用返回的数组，不需要 response.configs
      setRoleConfigs(Array.isArray(response) ? response : []);
    } catch (error) {
      console.error('获取角色配置失败:', error);
      message.error('获取角色配置失败');
    }
  };

  // 获取角色列表
  const fetchRoles = async () => {
    try {
      const response = await roleAPI.getRoles();
      // 直接使用返回的数组，不需要 response.roles
      setRoles(Array.isArray(response) ? response : []);
    } catch (error) {
      message.error('获取角色列表失败');
    }
  };

  // 保存系统配置
  const handleSaveSystemConfig = async (values) => {
    try {
      // 将config_value转换为字符串
      const configData = {
        ...values,
        config_value: String(values.config_value)
      };
      
      if (editingConfig) {
        await configAPI.updateSystemConfig(configData.config_key, {
          config_value: configData.config_value,
          description: configData.description
        });
        message.success('配置更新成功');
      } else {
        await configAPI.createSystemConfig(configData);
        message.success('配置添加成功');
      }
      setModalVisible(false);
      setEditingConfig(null);
      form.resetFields();
      fetchSystemConfigs();
    } catch (error) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // 保存角色配置
  const handleSaveRoleConfig = async (values) => {
    try {
      // 将config_value转换为字符串
      const configData = {
        ...values,
        config_value: String(values.config_value)
      };
      await configAPI.createRoleConfig(configData);
      message.success('角色配置保存成功');
      setRoleModalVisible(false);
      setEditingRoleConfig(null);
      roleForm.resetFields();
      fetchRoleConfigs();
    } catch (error) {
      message.error(error.response?.data?.detail || '操作失败');
    }
  };

  // 删除角色配置
  const handleDeleteRoleConfig = async (roleId, configKey) => {
    try {
      await configAPI.deleteRoleConfig(roleId, configKey);
      message.success('角色配置删除成功');
      fetchRoleConfigs();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 系统配置表格列
  const systemColumns = [
    {
      title: '配置项',
      dataIndex: 'config_key',
      key: 'config_key',
      render: (key) => CONFIG_TYPES[key]?.label || key
    },
    {
      title: '配置值',
      dataIndex: 'config_value',
      key: 'config_value',
      render: (value, record) => {
        const configType = CONFIG_TYPES[record.config_key];
        if (configType?.type === 'number' && value === -1) {
          return <span style={{ color: '#52c41a' }}>不限制</span>;
        }
        return value;
      }
    },
    {
      title: '描述',
      dataIndex: 'config_key',
      key: 'description',
      render: (key) => CONFIG_TYPES[key]?.description || '-'
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (time) => time ? new Date(time).toLocaleString() : '-'
    },
    ...(canManage ? [{
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingConfig(record);
              form.setFieldsValue(record);
              setModalVisible(true);
            }}
          >
            编辑
          </Button>
        </Space>
      )
    }] : [])
  ];

  // 角色配置表格列
  const roleColumns = [
    {
      title: '角色',
      dataIndex: 'role_id',
      key: 'role_id',
      render: (roleId) => {
        const role = roles.find(r => r.id === roleId);
        return role ? role.name : roleId;
      }
    },
    {
      title: '配置项',
      dataIndex: 'config_key',
      key: 'config_key',
      render: (key) => CONFIG_TYPES[key]?.label || key
    },
    {
      title: '配置值',
      dataIndex: 'config_value',
      key: 'config_value',
      render: (value, record) => {
        const configType = CONFIG_TYPES[record.config_key];
        if (configType?.type === 'number' && value === -1) {
          return <span style={{ color: '#52c41a' }}>不限制</span>;
        }
        return value;
      }
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (time) => time ? new Date(time).toLocaleString() : '-'
    },
    ...(canManage ? [{
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Popconfirm
            title="确定要删除这个角色配置吗？"
            onConfirm={() => handleDeleteRoleConfig(record.role_id, record.config_key)}
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
    }] : [])
  ];

  if (!canView) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <h3>您没有权限访问此页面</h3>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card title="配置管理" extra={
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={() => {
              fetchSystemConfigs();
              fetchRoleConfigs();
            }}
          >
            刷新
          </Button>
        </Space>
      }>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="系统配置" key="system">
            <div style={{ marginBottom: '16px' }}>
              {/* 移除添加配置按钮，因为系统配置是预定义的 */}
              {/* {canManage && (
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setEditingConfig(null);
                    form.resetFields();
                    setModalVisible(true);
                  }}
                >
                  添加配置
                </Button>
              )} */}
            </div>
            <Table
              columns={systemColumns}
              dataSource={systemConfigs}
              rowKey="config_key"
              loading={loading}
              scroll={{ x: 800, y: 400 }}
            />
          </TabPane>

          <TabPane tab="角色配置覆盖" key="role">
            <div style={{ marginBottom: '16px' }}>
              {canManage && (
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setEditingRoleConfig(null);
                    roleForm.resetFields();
                    setRoleModalVisible(true);
                  }}
                >
                  添加角色配置
                </Button>
              )}
            </div>
            <Table
              columns={roleColumns}
              dataSource={roleConfigs}
              rowKey={(record) => `${record.role_id}-${record.config_key}`}
              loading={loading}
              pagination={false}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 系统配置编辑模态框 */}
      <Modal
        title={editingConfig ? "编辑系统配置" : "添加系统配置"}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingConfig(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveSystemConfig}
        >
          <Form.Item
            name="config_key"
            label="配置项"
            rules={[{ required: true, message: '请选择配置项' }]}
          >
            <Select placeholder="选择配置项" disabled={!!editingConfig}>
              {Object.entries(CONFIG_TYPES).map(([key, config]) => (
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
            label="配置值"
            rules={[{ required: true, message: '请输入配置值' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="输入配置值"
              min={-1}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
              <Button onClick={() => {
                setModalVisible(false);
                setEditingConfig(null);
                form.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 角色配置编辑模态框 */}
      <Modal
        title="添加角色配置覆盖"
        open={roleModalVisible}
        onCancel={() => {
          setRoleModalVisible(false);
          setEditingRoleConfig(null);
          roleForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={roleForm}
          layout="vertical"
          onFinish={handleSaveRoleConfig}
        >
          <Form.Item
            name="role_id"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select placeholder="选择角色">
              {roles.map(role => (
                <Option key={role.id} value={role.id}>
                  {role.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="config_key"
            label="配置项"
            rules={[{ required: true, message: '请选择配置项' }]}
          >
            <Select placeholder="选择配置项">
              {Object.entries(CONFIG_TYPES).map(([key, config]) => (
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
            label="配置值"
            rules={[{ required: true, message: '请输入配置值' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="输入配置值"
              min={-1}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
              <Button onClick={() => {
                setRoleModalVisible(false);
                setEditingRoleConfig(null);
                roleForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ConfigManagement;