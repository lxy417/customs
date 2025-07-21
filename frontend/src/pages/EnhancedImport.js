import React, { useState, useEffect } from 'react';
import { 
  Upload, Button, Card, Typography, message, Progress, Space, Alert, 
  Table, Tag, Tabs, Statistic, Row, Col, Modal, Descriptions, Select,
  Pagination, Tooltip, Divider, List, Badge
} from 'antd';
import { 
  UploadOutlined, FileExcelOutlined, HistoryOutlined, 
  BarChartOutlined, EyeOutlined, ReloadOutlined, SettingOutlined,
  CheckCircleOutlined, CloseCircleOutlined, SyncOutlined
} from '@ant-design/icons';
import { enhancedImportAPI } from '../utils/api';
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

  // 历史记录表格列定义
  const historyColumns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 120,
      render: (text) => <Text code>{text}</Text>
    },
    {
      title: '文件名',
      dataIndex: 'original_filename',
      key: 'original_filename',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusConfig = {
          'processing': { color: 'blue', icon: <SyncOutlined spin />, text: '处理中' },
          'completed': { color: 'green', icon: <CheckCircleOutlined />, text: '完成' },
          'failed': { color: 'red', icon: <CloseCircleOutlined />, text: '失败' }
        };
        const config = statusConfig[status] || { color: 'default', text: status };
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      }
    },
    {
      title: '海关编码',
      dataIndex: 'customs_codes',
      key: 'customs_codes',
      width: 120,
      render: (codes) => codes ? codes.join(', ') : '-'
    },
    {
      title: '数据日期范围',
      key: 'date_range',
      width: 180,
      render: (_, record) => {
        if (record.start_date && record.end_date) {
          return `${record.start_date} ~ ${record.end_date}`;
        }
        return '-';
      }
    },
    {
      title: '成功/总数',
      key: 'success_rate',
      width: 120,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text>{record.success_count || 0} / {record.total_count || 0}</Text>
          <Progress 
            percent={record.total_count ? Math.round((record.success_count || 0) / record.total_count * 100) : 0}
            size="small"
            showInfo={false}
          />
        </Space>
      )
    },
    {
      title: '导入时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time) => moment(time).format('YYYY-MM-DD HH:mm')
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button 
          type="link" 
          icon={<EyeOutlined />}
          onClick={() => viewTaskDetail(record.task_id)}
        >
          详情
        </Button>
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
                <Tag color={selectedTask.status === 'completed' ? 'green' : selectedTask.status === 'failed' ? 'red' : 'blue'}>
                  {selectedTask.status === 'completed' ? '完成' : selectedTask.status === 'failed' ? '失败' : '处理中'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="原始文件名">{selectedTask.original_filename}</Descriptions.Item>
              <Descriptions.Item label="处理文件数">{selectedTask.processed_files?.length || 0}</Descriptions.Item>
              <Descriptions.Item label="成功记录数">{selectedTask.success_count}</Descriptions.Item>
              <Descriptions.Item label="失败记录数">{selectedTask.failed_count}</Descriptions.Item>
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
                            <Badge count={file.success_count} style={{ backgroundColor: '#52c41a' }} />
                            <span>成功</span>
                            <Badge count={file.failed_count} style={{ backgroundColor: '#f5222d' }} />
                            <span>失败</span>
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
    </div>
  );
};

export default EnhancedImport;