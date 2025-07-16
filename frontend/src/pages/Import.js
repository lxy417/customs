import React, { useState } from 'react';
import { Upload, Button, Card, Typography, message, Progress, Space, Alert } from 'antd';
import { UploadOutlined, FileExcelOutlined } from '@ant-design/icons';
import { importAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';

const { Title, Text } = Typography;

const Import = () => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState(null); // null, 'success', 'error'
  const [uploadMessage, setUploadMessage] = useState('');
  const { user } = useAuth();

  // 处理文件上传
  const handleUpload = async (file) => {
    setUploading(true);
    setProgress(0);
    setUploadStatus(null);
    setUploadMessage('');

    try {
      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + 10;
          if (newProgress >= 90) {
            clearInterval(progressInterval);
          }
          return newProgress;
        });
      }, 500);

      // 调用API上传文件
      const response = await importAPI.importExcel(file);
      clearInterval(progressInterval);
      setProgress(100);
      setUploadStatus('success');
      setUploadMessage(response.message || '文件上传成功，数据导入任务已启动');
      message.success('文件上传成功，数据导入任务已启动');
    } catch (error) {
      setUploadStatus('error');
      setUploadMessage(error.response?.data?.detail || '文件上传失败，请重试');
      message.error('文件上传失败，请重试');
    } finally {
      setUploading(false);
      // 3秒后重置进度条
      setTimeout(() => {
        if (uploadStatus === 'success') {
          setProgress(0);
          setUploadStatus(null);
        }
      }, 3000);
    }

    return false; // 阻止默认上传行为
  };

  // 上传按钮配置
  const uploadButton = (
    <Button
      icon={<UploadOutlined />}
      disabled={uploading}
      loading={uploading}
      type="primary"
      size="large"
    >
      选择Excel文件
    </Button>
  );

  return (
    <div className="import-page">
      <Title level={2}>数据导入</Title>
      <Card className="import-card">
        <div className="import-container">
          <div className="upload-area">
            <Upload
              name="file"
              beforeUpload={handleUpload}
              showUploadList={false}
              accept=".xlsx,.xls"
            >
              <div className="upload-button-container">
                {uploadButton}
                <Text type="secondary" style={{ display: 'block', marginTop: 16 }}>
                  支持 .xlsx 和 .xls 格式文件
                </Text>
              </div>
            </Upload>
          </div>

          {progress > 0 && (
            <div className="progress-container">
              <Progress
                percent={progress}
                status={uploadStatus || 'active'}
                size="small"
                strokeWidth={3}
              />
              {uploadMessage && (
                <Text
                  style={{
                    marginTop: 8,
                    display: 'block',
                    color: uploadStatus === 'error' ? 'red' : 'inherit'
                  }}
                >
                  {uploadMessage}
                </Text>
              )}
            </div>
          )}

          {uploadStatus === 'error' && (
            <Alert
              message="上传失败"
              description={uploadMessage}
              type="error"
              showIcon
              style={{ marginTop: 16 }}
            />
          )}

          <div className="import-instructions" style={{ marginTop: 32 }}>
            <Title level={4}>导入说明</Title>
            <ul style={{ lineHeight: '1.8' }}>
              <li>请确保Excel文件包含系统要求的所有字段</li>
              <li>文件大小请勿超过10MB</li>
              <li>数据导入为后台任务，大文件可能需要较长时间处理</li>
              <li>导入完成后，您可以在数据查询页面查看导入的数据</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Import;