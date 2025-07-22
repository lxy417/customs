import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  message,
  Space,
  Card,
  Row,
  Col,
  Popconfirm,
  Tag,
  Upload,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExportOutlined,
  ImportOutlined,
  SearchOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { dataAPI } from '../utils/api';
import { usePermissions } from '../context/PermissionContext';
import PermissionButton from '../components/PermissionButton';
import PermissionWrapper from '../components/PermissionWrapper';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { Search } = Input;

const DataManagement = () => {
  const { hasPermission, hasCustomsCodeAccess, isAdmin, PERMISSIONS } = usePermissions();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('create');
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [searchParams, setSearchParams] = useState({});
  const [customsCodes, setCustomsCodes] = useState([]);
  const [importers, setImporters] = useState([]);
  const [exporters, setExporters] = useState([]);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchData();
    fetchCustomsCodes();
    fetchImporters();
    fetchExporters();
  }, []);

  const fetchData = async (params = {}) => {
    try {
      setLoading(true);
      const response = await dataAPI.searchData(params);
      setData(response.data || []);
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomsCodes = async () => {
    try {
      const response = await dataAPI.getCustomsCodes();
      setCustomsCodes(response);
    } catch (error) {
      console.error('获取海关编码失败:', error);
    }
  };

  const fetchImporters = async () => {
    try {
      const response = await dataAPI.getImporters();
      setImporters(response);
    } catch (error) {
      console.error('获取进口商失败:', error);
    }
  };

  const fetchExporters = async () => {
    try {
      const response = await dataAPI.getExporters();
      setExporters(response);
    } catch (error) {
      console.error('获取出口商失败:', error);
    }
  };

  const handleSearch = (values) => {
    setSearchParams(values);
    fetchData(values);
  };

  const handleCreate = () => {
    setModalType('create');
    setSelectedRecord(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    // 检查是否有权限编辑该海关编码的数据
    if (!isAdmin() && !hasCustomsCodeAccess(record.customs_code)) {
      message.error('您没有权限编辑该海关编码的数据');
      return;
    }

    setModalType('edit');
    setSelectedRecord(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (record) => {
    // 检查是否有权限删除该海关编码的数据
    if (!isAdmin() && !hasCustomsCodeAccess(record.customs_code)) {
      message.error('您没有权限删除该海关编码的数据');
      return;
    }

    try {
      await dataAPI.deleteData(record.id);
      message.success('删除成功');
      fetchData(searchParams);
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的数据');
      return;
    }

    try {
      await dataAPI.bulkDeleteData(selectedRowKeys);
      message.success('批量删除成功');
      setSelectedRowKeys([]);
      fetchData(searchParams);
    } catch (error) {
      message.error('批量删除失败');
    }
  };

  const handleExport = async () => {
    try {
      const response = await dataAPI.exportData(searchParams);
      // 处理文件下载
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `customs_data_${new Date().getTime()}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    }
  };

  const handleSubmit = async (values) => {
    try {
      if (modalType === 'create') {
        await dataAPI.createData(values);
        message.success('创建成功');
      } else {
        await dataAPI.updateData(selectedRecord.id, values);
        message.success('更新成功');
      }
      setModalVisible(false);
      fetchData(searchParams);
    } catch (error) {
      message.error(`${modalType === 'create' ? '创建' : '更新'}失败`);
    }
  };

  const columns = [
    {
      title: '海关编码',
      dataIndex: 'customs_code',
      key: 'customs_code',
      render: (text) => (
        <Tag color={hasCustomsCodeAccess(text) ? 'green' : 'red'}>
          {text}
        </Tag>
      )
    },
    {
      title: '商品名称',
      dataIndex: 'product_name',
      key: 'product_name',
    },
    {
      title: '进口商',
      dataIndex: 'importer',
      key: 'importer',
    },
    {
      title: '出口商',
      dataIndex: 'exporter',
      key: 'exporter',
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '单位',
      dataIndex: 'unit',
      key: 'unit',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <PermissionButton
            type="link"
            icon={<EditOutlined />}
            permission={PERMISSIONS.DATA_UPDATE}
            customsCode={record.customs_code}
            onClick={() => handleEdit(record)}
          >
            编辑
          </PermissionButton>
          <PermissionButton
            type="link"
            danger
            icon={<DeleteOutlined />}
            permission={PERMISSIONS.DATA_DELETE}
            customsCode={record.customs_code}
            onClick={() => handleDelete(record)}
          >
            删除
          </PermissionButton>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
    getCheckboxProps: (record) => ({
      disabled: !hasPermission(PERMISSIONS.DATA_DELETE) || 
                (!isAdmin() && !hasCustomsCodeAccess(record.customs_code))
    }),
  };

  return (
    <div>
      <Card>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Space wrap>
              <PermissionButton
                type="primary"
                icon={<PlusOutlined />}
                permission={PERMISSIONS.DATA_CREATE}
                onClick={handleCreate}
              >
                新增数据
              </PermissionButton>
              
              <PermissionButton
                danger
                icon={<DeleteOutlined />}
                permission={PERMISSIONS.DATA_DELETE}
                disabled={selectedRowKeys.length === 0}
                onClick={handleBulkDelete}
              >
                批量删除
              </PermissionButton>
              
              <PermissionButton
                icon={<ExportOutlined />}
                permission={PERMISSIONS.DATA_EXPORT}
                onClick={handleExport}
              >
                导出数据
              </PermissionButton>
              
              <PermissionWrapper permission={PERMISSIONS.DATA_CREATE} showForbidden={false}>
                <Upload
                  accept=".xlsx,.xls"
                  showUploadList={false}
                  beforeUpload={() => false}
                >
                  <Button icon={<ImportOutlined />}>
                    导入数据
                  </Button>
                </Upload>
              </PermissionWrapper>
            </Space>
          </Col>
          
          <Col span={24}>
            <Form
              layout="inline"
              onFinish={handleSearch}
            >
              <Form.Item name="query">
                <Search
                  placeholder="搜索关键词"
                  style={{ width: 200 }}
                  allowClear
                />
              </Form.Item>
              
              <Form.Item name="customs_code">
                <Select
                  placeholder="选择海关编码"
                  style={{ width: 150 }}
                  allowClear
                  showSearch
                >
                  {customsCodes.map(code => (
                    <Option key={code} value={code}>
                      {code}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              
              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                  搜索
                </Button>
              </Form.Item>
            </Form>
          </Col>
        </Row>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          rowSelection={hasPermission(PERMISSIONS.DATA_DELETE) ? rowSelection : null}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 创建/编辑模态框 */}
      <Modal
        title={modalType === 'create' ? '新增数据' : '编辑数据'}
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
            name="customs_code"
            label="海关编码"
            rules={[{ required: true, message: '请选择海关编码' }]}
          >
            <Select
              placeholder="请选择海关编码"
              showSearch
              disabled={modalType === 'edit'}
            >
              {customsCodes
                .filter(code => isAdmin() || hasCustomsCodeAccess(code))
                .map(code => (
                  <Option key={code} value={code}>
                    {code}
                  </Option>
                ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="product_name"
            label="商品名称"
            rules={[{ required: true, message: '请输入商品名称' }]}
          >
            <Input placeholder="请输入商品名称" />
          </Form.Item>

          <Form.Item
            name="importer"
            label="进口商"
            rules={[{ required: true, message: '请选择进口商' }]}
          >
            <Select
              placeholder="请选择进口商"
              showSearch
              allowClear
            >
              {importers.map(importer => (
                <Option key={importer} value={importer}>
                  {importer}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="exporter"
            label="出口商"
            rules={[{ required: true, message: '请选择出口商' }]}
          >
            <Select
              placeholder="请选择出口商"
              showSearch
              allowClear
            >
              {exporters.map(exporter => (
                <Option key={exporter} value={exporter}>
                  {exporter}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="quantity"
            label="数量"
            rules={[{ required: true, message: '请输入数量' }]}
          >
            <Input type="number" placeholder="请输入数量" />
          </Form.Item>

          <Form.Item
            name="unit"
            label="单位"
            rules={[{ required: true, message: '请输入单位' }]}
          >
            <Input placeholder="请输入单位" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {modalType === 'create' ? '创建' : '更新'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DataManagement;