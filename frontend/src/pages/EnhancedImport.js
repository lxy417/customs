import React, { useState, useEffect } from 'react';
import { 
  Upload, Button, Card, Typography, message, Progress, Space, Alert, 
  Table, Tag, Tabs, Statistic, Row, Col, Modal, Descriptions, Select,
  Pagination, Tooltip, Divider, List, Badge, Steps
} from 'antd';
import { 
  UploadOutlined, FileExcelOutlined, HistoryOutlined, 
  BarChartOutlined, EyeOutlined, ReloadOutlined, SettingOutlined,
  CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, RollbackOutlined,
  ExclamationCircleOutlined, InfoCircleOutlined
} from '@ant-design/icons';
import { enhancedImportAPI, rollbackAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import moment from 'moment';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

const EnhancedImport = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [batchSize, setBatchSize] = useState(500);
  const [activeTab, setActiveTab] = useState('upload');
  
  // 文件列表状态
  const [fileList, setFileList] = useState([]);
  
  // 历史记录相关状态
  const [historyData, setHistoryData] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyPagination, setHistoryPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [statusFilter, setStatusFilter] = useState(null);
  
  // 统计信息状态
  const [statistics, setStatistics] = useState({
    totalImports: 0,
    successfulImports: 0,
    failedImports: 0,
    totalRecords: 0
  });
  
  // 任务详情模态框
  const [taskDetailVisible, setTaskDetailVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  
  // 回滚相关状态
  const [rollbackModalVisible, setRollbackModalVisible] = useState(false);
  const [rollbackPreview, setRollbackPreview] = useState(null);
  const [rollbackLoading, setRollbackLoading] = useState(false);
  const [selectedRollbackTask, setSelectedRollbackTask] = useState(null);
  
  const { user } = useAuth();

  // 组件加载时获取数据
  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistoryData();
    } else if (activeTab === 'statistics') {
      fetchStatistics();
    }
  }, [activeTab, historyPagination.current, statusFilter]);

  // 获取历史记录
  const fetchHistoryData = async () => {
    setHistoryLoading(true);
    try {
      const response = await enhancedImportAPI.getImportHistory({
        page: historyPagination.current,
        page_size: historyPagination.pageSize,
        status: statusFilter
      });
      setHistoryData(response.data || []);
      setHistoryPagination(prev => ({
        ...prev,
        total: response.total || 0
      }));
    } catch (error) {
      message.error('获取导入历史失败');
    } finally {
      setHistoryLoading(false);
    }
  };

  // 获取统计信息
  const fetchStatistics = async () => {
    try {
      const response = await enhancedImportAPI.getImportStatistics();
      setStatistics(response);
    } catch (error) {
      message.error('获取统计信息失败');
    }
  };

  // 处理文件上传
  const handleUpload = async () => {
    if (!fileList || fileList.length === 0) {
      message.warning('请选择要上传的文件');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadStatus('uploading');
    setUploadMessage('正在上传文件...');

    try {
      const formData = new FormData();
      fileList.forEach(file => {
        formData.append('files', file.originFileObj || file);
      });
      formData.append('batch_size', batchSize);

      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const newProgress = prev + 10;
          if (newProgress >= 90) {
            clearInterval(progressInterval);
          }
          return newProgress;
        });
      }, 500);

      const response = await enhancedImportAPI.uploadFiles(formData);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadStatus('success');
      setUploadMessage(`文件上传成功！任务ID: ${response.task_id}`);
      
      message.success('文件上传成功，开始处理数据');
      
      // 清空文件列表
      setFileList([]);
      
      // 刷新历史记录
      if (activeTab === 'history') {
        fetchHistoryData();
      }
      
    } catch (error) {
      setUploadStatus('error');
      setUploadMessage(error.response?.data?.detail || '上传失败');
      message.error('文件上传失败');
    } finally {
      setUploading(false);
    }
  };

  // 查看任务详情
  const viewTaskDetail = async (taskId) => {
    try {
      const response = await enhancedImportAPI.getTaskDetail(taskId);
      setSelectedTask(response);
      setTaskDetailVisible(true);
    } catch (error) {
      message.error('获取任务详情失败');
    }
  };

  // 回滚操作函数
  const handleRollbackPreview = async (taskId) => {
    try {
      setRollbackLoading(true);
      const result = await rollbackAPI.previewRollback(taskId);
      if (result.success) {
        setRollbackPreview(result.preview);
        setSelectedRollbackTask(taskId);
        setRollbackModalVisible(true);
      } else {
        message.error(result.error || '预览回滚失败');
      }
    } catch (error) {
      message.error('预览回滚失败');
    } finally {
      setRollbackLoading(false);
    }
  };

  const handleRollbackExecute = async (dryRun = false) => {
    try {
      setRollbackLoading(true);
      const result = await rollbackAPI.executeRollback(selectedRollbackTask, dryRun);
      if (result.success) {
        message.success(dryRun ? '回滚预演成功' : '回滚执行成功');
        setRollbackModalVisible(false);
        fetchHistoryData(); // 刷新历史记录
      } else {
        message.error(result.error || '回滚失败');
      }
    } catch (error) {
      message.error('回滚操作失败');
    } finally {
      setRollbackLoading(false);
    }
  };

  // 统一的状态配置函数
  const getStatusConfig = (status) => {
    const statusConfigs = {
      'processing': { 
        color: 'blue', 
        icon: <SyncOutlined spin />, 
        text: '处理中',
        description: '数据正在处理中...'
      },
      'completed': { 
        color: 'green', 
        icon: <CheckCircleOutlined />, 
        text: '完成',
        description: '数据导入成功完成'
      },
      'failed': { 
        color: 'red', 
        icon: <CloseCircleOutlined />, 
        text: '失败',
        description: '数据导入失败'
      },
      'rolled_back': { 
        color: 'orange', 
        icon: <RollbackOutlined />, 
        text: '已回滚',
        description: '数据已被回滚删除'
      },
      'rollback_pending': { 
        color: 'purple', 
        icon: <SyncOutlined spin />, 
        text: '回滚中',
        description: '正在执行回滚操作'
      },
      'rollback_failed': { 
        color: 'volcano', 
        icon: <ExclamationCircleOutlined />, 
        text: '回滚失败',
        description: '回滚操作执行失败'
      }
    };
    return statusConfigs[status] || { 
      color: 'default', 
      icon: <InfoCircleOutlined />, 
      text: status || '未知',
      description: '未知状态'
    };
  };

  // 历史记录表格列定义
  const historyColumns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200,
      render: (text) => <Text code>{text}</Text>
    },
    {
      title: '文件名',
      dataIndex: 'original_filename',
      key: 'original_filename',
      width: 200,
      ellipsis: true
    },
    {
      title: '上传用户',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 120
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => {
        const config = getStatusConfig(status);
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      }
    },
    {
      title: '海关编码',
      dataIndex: 'customs_code',
      key: 'customs_code',
      width: 100,
      render: (text) => {
        if (!text) return '-';
        return <Tag color="blue">{text}</Tag>;
      }
    },
    {
      title: '数据日期范围',
      key: 'date_range',
      width: 200,
      render: (_, record) => {
        // 尝试多种可能的数据结构
        let startDate = null;
        let endDate = null;
        
        if (record.date_range) {
          startDate = record.date_range.start || record.date_range.start_date;
          endDate = record.date_range.end || record.date_range.end_date;
        } else if (record.start_date && record.end_date) {
          startDate = record.start_date;
          endDate = record.end_date;
        } else if (record.date_start && record.date_end) {
          startDate = record.date_start;
          endDate = record.date_end;
        }
        
        if (startDate && endDate) {
          return (
            <div>
              <div><Text type="secondary">开始:</Text> {startDate}</div>
              <div><Text type="secondary">结束:</Text> {endDate}</div>
            </div>
          );
        }
        return <Text type="secondary">-</Text>;
      }
    },
    {
      title: '处理结果',
      key: 'processing_result',
      width: 180,
      render: (_, record) => {
        const successCount = record.success_count || record.successful_count || 0;
        const duplicateCount = record.duplicate_count || record.duplicated_count || 0;
        const failedCount = record.failed_count || record.error_count || 0;
        const totalCount = record.original_total_count || record.total_count || 0;
        
        return (
          <div style={{ fontSize: '12px', lineHeight: '1.4' }}>
            <div style={{ marginBottom: '2px' }}>
              <span style={{ color: '#52c41a', fontWeight: 'bold' }}>✓ 成功: </span>
              <span>{successCount.toLocaleString()}</span>
            </div>
            <div style={{ marginBottom: '2px' }}>
              <span style={{ color: '#faad14', fontWeight: 'bold' }}>⚠ 重复: </span>
              <span>{duplicateCount.toLocaleString()}</span>
            </div>
            <div style={{ marginBottom: '2px' }}>
              <span style={{ color: '#f5222d', fontWeight: 'bold' }}>✗ 失败: </span>
              <span>{failedCount.toLocaleString()}</span>
            </div>
            <Divider style={{ margin: '4px 0' }} />
            <div style={{ color: '#666', fontWeight: 'bold' }}>
              <span>总计: {totalCount.toLocaleString()}</span>
            </div>
          </div>
        );
      }
    },
    {
      title: '导入时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time) => moment(time).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            size="small"
            icon={<EyeOutlined />}
            onClick={() => viewTaskDetail(record.task_id)}
          >
            详情
          </Button>
          {record.status === 'completed' && !record.rollback_status && (
            <Button 
              type="link" 
              size="small"
              danger
              icon={<RollbackOutlined />}
              onClick={() => handleRollbackPreview(record.task_id)}
            >
              回滚
            </Button>
          )}
        </Space>
      )
    }
  ];

  // 上传配置
  const uploadProps = {
    multiple: true,
    accept: '.xlsx,.xls',
    beforeUpload: () => false, // 阻止自动上传
    showUploadList: true,
    listType: 'text',
    fileList: fileList,
    onChange: ({ fileList: newFileList }) => {
      setFileList(newFileList);
    },
    onRemove: (file) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    }
  };

  // 回滚模态框组件
  const RollbackModal = () => (
    <Modal
      title={
        <Space>
          <RollbackOutlined style={{ color: '#ff4d4f' }} />
          <span>数据回滚确认</span>
        </Space>
      }
      visible={rollbackModalVisible}
      onCancel={() => setRollbackModalVisible(false)}
      footer={[
        <Button key="cancel" onClick={() => setRollbackModalVisible(false)}>
          取消
        </Button>,
        <Button 
          key="preview" 
          onClick={() => handleRollbackExecute(true)}
          loading={rollbackLoading}
          icon={<EyeOutlined />}
        >
          预演回滚
        </Button>,
        <Button 
          key="execute" 
          type="primary" 
          danger
          onClick={() => handleRollbackExecute(false)}
          loading={rollbackLoading}
          icon={<RollbackOutlined />}
        >
          确认回滚
        </Button>
      ]}
      width={900}
    >
      {rollbackPreview && (
        <div>
          <Alert
            message="⚠️ 重要警告"
            description="回滚操作将永久删除导入的数据，此操作不可逆转，请谨慎操作！"
            type="warning"
            showIcon
            style={{ marginBottom: 24 }}
          />
          
          {/* 回滚进度步骤 */}
          <Steps
            current={0}
            size="small"
            style={{ marginBottom: 24 }}
            items={[
              {
                title: '预览数据',
                description: '查看将要删除的数据',
                icon: <EyeOutlined />
              },
              {
                title: '确认回滚',
                description: '执行回滚操作',
                icon: <RollbackOutlined />
              },
              {
                title: '完成',
                description: '回滚操作完成',
                icon: <CheckCircleOutlined />
              }
            ]}
          />
          
          {/* 任务信息卡片 */}
          <Card 
            title="任务信息" 
            size="small" 
            style={{ marginBottom: 16 }}
            extra={<Tag color="blue">任务详情</Tag>}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Descriptions size="small" column={1}>
                  <Descriptions.Item label="任务ID">
                    <Text code>{rollbackPreview.task_info.task_id}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="原始文件">
                    <Text strong>{rollbackPreview.task_info.original_filename}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="导入用户">
                    <Tag color="geekblue">{rollbackPreview.task_info.user_id}</Tag>
                  </Descriptions.Item>
                </Descriptions>
              </Col>
              <Col span={12}>
                <Descriptions size="small" column={1}>
                  <Descriptions.Item label="导入时间">
                    {moment(rollbackPreview.task_info.created_at).format('YYYY-MM-DD HH:mm:ss')}
                  </Descriptions.Item>
                  <Descriptions.Item label="处理状态">
                    <Tag color="green">已完成</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="数据状态">
                    <Tag color="orange">待回滚</Tag>
                  </Descriptions.Item>
                </Descriptions>
              </Col>
            </Row>
          </Card>
          
          {/* 回滚统计信息 */}
          <Card 
            title="回滚统计" 
            size="small" 
            style={{ marginBottom: 16 }}
            extra={<Tag color="volcano">数据统计</Tag>}
          >
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="总导入文档"
                  value={rollbackPreview.rollback_summary.total_imported_docs}
                  valueStyle={{ color: '#1890ff' }}
                  prefix={<FileExcelOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="现存文档"
                  value={rollbackPreview.rollback_summary.existing_docs}
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<CheckCircleOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="将被删除"
                  value={rollbackPreview.rollback_summary.will_be_deleted}
                  valueStyle={{ color: '#ff4d4f' }}
                  prefix={<CloseCircleOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="已缺失文档"
                  value={rollbackPreview.rollback_summary.missing_docs}
                  valueStyle={{ color: '#faad14' }}
                  prefix={<ExclamationCircleOutlined />}
                />
              </Col>
            </Row>
          </Card>
          
          {/* 数据样本预览 */}
          {rollbackPreview.sample_data && rollbackPreview.sample_data.length > 0 && (
            <Card 
              title="数据样本预览" 
              size="small"
              extra={<Tag color="purple">前5条数据</Tag>}
            >
              <Table
                dataSource={rollbackPreview.sample_data.map((item, index) => ({
                  key: index,
                  id: item.id,
                  customs_code: item.source.海关编码,
                  product_name: item.source.详细产品名称,
                  country: item.source.国家,
                  date: item.source.数据日期
                }))}
                columns={[
                  {
                    title: '文档ID',
                    dataIndex: 'id',
                    key: 'id',
                    width: 200,
                    render: (text) => <Text code style={{ fontSize: '12px' }}>{text}</Text>
                  },
                  {
                    title: '海关编码',
                    dataIndex: 'customs_code',
                    key: 'customs_code',
                    width: 100,
                    render: (text) => <Tag color="blue">{text}</Tag>
                  },
                  {
                    title: '产品名称',
                    dataIndex: 'product_name',
                    key: 'product_name',
                    ellipsis: true,
                    render: (text) => <Text>{text}</Text>
                  },
                  {
                    title: '国家',
                    dataIndex: 'country',
                    key: 'country',
                    width: 80,
                    render: (text) => <Tag color="geekblue">{text}</Tag>
                  },
                  {
                    title: '数据日期',
                    dataIndex: 'date',
                    key: 'date',
                    width: 100,
                    render: (text) => <Text>{text}</Text>
                  }
                ]}
                pagination={false}
                size="small"
                scroll={{ y: 200 }}
              />
            </Card>
          )}
          
          {/* 操作提示 */}
          <Alert
            message="操作说明"
            description={
              <div>
                <p>• <strong>预演回滚</strong>：模拟回滚过程，不会实际删除数据</p>
                <p>• <strong>确认回滚</strong>：正式执行回滚，将永久删除上述数据</p>
                <p>• 回滚完成后，任务状态将变更为"已回滚"</p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        </div>
      )}
    </Modal>
  );

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <FileExcelOutlined /> 数据导入管理
      </Title>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* 文件上传标签页 */}
        <TabPane tab={<span><UploadOutlined />文件上传</span>} key="upload">
          <Row gutter={24}>
            <Col span={16}>
              <Card title="批量文件上传" extra={
                <Space>
                  <Text>批量大小:</Text>
                  <Select 
                    value={batchSize} 
                    onChange={setBatchSize}
                    style={{ width: 100 }}
                  >
                    <Option value={100}>100</Option>
                    <Option value={500}>500</Option>
                    <Option value={1000}>1000</Option>
                  </Select>
                </Space>
              }>
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Alert
                    message="上传说明"
                    description={
                      <div>
                        <p>• 支持同时上传多个Excel文件(.xlsx, .xls)</p>
                        <p>• 系统会自动处理每个文件的多个sheet</p>
                        <p>• 自动进行数据去重和格式转换</p>
                        <p>• 海关编码会自动截取前6位</p>
                        <p>• 国家名称会自动转换为中文</p>
                        <p>• 自动检测ES数据库中的重复数据</p>
                      </div>
                    }
                    type="info"
                    showIcon
                  />
                  
                  <Upload.Dragger {...uploadProps}>
                    <p className="ant-upload-drag-icon">
                      <FileExcelOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
                    </p>
                    <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                    <p className="ant-upload-hint">支持单个或批量上传Excel文件</p>
                  </Upload.Dragger>
                  
                  <Button 
                    type="primary" 
                    size="large"
                    loading={uploading}
                    onClick={handleUpload}
                    disabled={fileList.length === 0}
                    block
                  >
                    {uploading ? '上传中...' : `开始上传 (${fileList.length} 个文件)`}
                  </Button>
                </Space>
              </Card>
            </Col>
            
            <Col span={8}>
              <Card title="上传进度">
                {uploadStatus && (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Progress 
                      percent={uploadProgress} 
                      status={uploadStatus === 'error' ? 'exception' : 'active'}
                    />
                    <Alert
                      message={uploadMessage}
                      type={uploadStatus === 'success' ? 'success' : uploadStatus === 'error' ? 'error' : 'info'}
                      showIcon
                    />
                  </Space>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* 历史记录标签页 */}
        <TabPane tab={<span><HistoryOutlined />导入历史</span>} key="history">
          <Card 
            title="导入历史记录" 
            extra={
              <Space>
                <Select
                  placeholder="筛选状态"
                  allowClear
                  style={{ width: 120 }}
                  value={statusFilter}
                  onChange={setStatusFilter}
                >
                  <Option value="processing">处理中</Option>
                  <Option value="completed">完成</Option>
                  <Option value="failed">失败</Option>
                  <Option value="rolled_back">已回滚</Option>
                  <Option value="rollback_pending">回滚中</Option>
                  <Option value="rollback_failed">回滚失败</Option>
                </Select>
                <Button icon={<ReloadOutlined />} onClick={fetchHistoryData}>
                  刷新
                </Button>
              </Space>
            }
          >
            <Table
              columns={historyColumns}
              dataSource={historyData}
              loading={historyLoading}
              rowKey="task_id"
              scroll={{ x: 1500, y: 600 }}
              pagination={{
                ...historyPagination,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`,
                onChange: (page, pageSize) => {
                  setHistoryPagination(prev => ({
                    ...prev,
                    current: page,
                    pageSize
                  }));
                }
              }}
            />
          </Card>
        </TabPane>

        {/* 统计信息标签页 */}
        <TabPane tab={<span><BarChartOutlined />统计信息</span>} key="statistics">
          <Row gutter={24}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总导入次数"
                  value={statistics.totalImports}
                  prefix={<UploadOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="成功导入"
                  value={statistics.successfulImports}
                  valueStyle={{ color: '#3f8600' }}
                  prefix={<CheckCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="失败导入"
                  value={statistics.failedImports}
                  valueStyle={{ color: '#cf1322' }}
                  prefix={<CloseCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="总记录数"
                  value={statistics.totalRecords}
                  prefix={<BarChartOutlined />}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* 任务详情模态框 */}
      <Modal
        title="任务详情"
        visible={taskDetailVisible}
        onCancel={() => setTaskDetailVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTask && (
          <div>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="任务ID">{selectedTask.task_id}</Descriptions.Item>
              <Descriptions.Item label="状态">
                {(() => {
                  const config = getStatusConfig(selectedTask.status);
                  return (
                    <Tag color={config.color} icon={config.icon}>
                      {config.text}
                    </Tag>
                  );
                })()}
              </Descriptions.Item>
              <Descriptions.Item label="原始文件名">{selectedTask.original_filename}</Descriptions.Item>
              <Descriptions.Item label="上传用户">{selectedTask.user_id}</Descriptions.Item>
              <Descriptions.Item label="处理文件数">{selectedTask.processed_files?.length || 0}</Descriptions.Item>
              <Descriptions.Item label="原文件总数">{selectedTask.original_total_count || 0}</Descriptions.Item>
              <Descriptions.Item label="成功记录数">{selectedTask.success_count || 0}</Descriptions.Item>
              <Descriptions.Item label="重复记录数">{selectedTask.duplicate_count || 0}</Descriptions.Item>
              <Descriptions.Item label="失败记录数">{selectedTask.failed_count || 0}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{moment(selectedTask.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
              <Descriptions.Item label="完成时间">
                {selectedTask.completed_at ? moment(selectedTask.completed_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
              </Descriptions.Item>
            </Descriptions>

            {selectedTask.processed_files && selectedTask.processed_files.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Title level={4}>处理文件列表</Title>
                <List
                  dataSource={selectedTask.processed_files}
                  renderItem={file => (
                    <List.Item>
                      <List.Item.Meta
                        title={file.filename}
                        description={
                          <Space>
                            <Badge count={file.success_count || 0} style={{ backgroundColor: '#52c41a' }} />
                            <span>成功</span>
                            <Badge count={file.duplicate_count || 0} style={{ backgroundColor: '#faad14' }} />
                            <span>重复</span>
                            <Badge count={file.failed_count || 0} style={{ backgroundColor: '#f5222d' }} />
                            <span>失败</span>
                            <Badge count={file.original_total_count || 0} style={{ backgroundColor: '#1890ff' }} />
                            <span>原文件总数</span>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              </div>
            )}

            {selectedTask.error_details && selectedTask.error_details.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Title level={4}>错误详情</Title>
                <List
                  dataSource={selectedTask.error_details}
                  renderItem={error => (
                    <List.Item>
                      <Alert
                        message={error.error_type}
                        description={error.error_message}
                        type="error"
                        showIcon
                      />
                    </List.Item>
                  )}
                />
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* 回滚模态框 */}
      <RollbackModal />
    </div>
  );
};

export default EnhancedImport;