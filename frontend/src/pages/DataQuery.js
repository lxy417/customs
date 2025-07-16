import React, { useState, useEffect } from 'react';
import { Form, Input, Select, DatePicker, Button, Table, Space, Typography, Card, Spin, message, Row, Col } from 'antd';
import { SearchOutlined, ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import { dataAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import moment from 'moment';
moment.locale('zh-cn');

const { Title } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const DataQuery = () => {
  const [form] = Form.useForm();
  const [dataSource, setDataSource] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [pagination, setPagination] = useState({
    total: 0,
    total_pages: 0,
    current: 1,
    pageSize: 20,
    showSizeChanger: true,
    showTotal: (total) => `共 ${total} 条记录，共 ${pagination.total_pages} 页`
  });
  const [customsCodes, setCustomsCodes] = useState([]);
  const [countries, setCountries] = useState({ import: [], export: [] });
  const { user } = useAuth();

  // 获取海关编码和国家列表
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        setLoading(true);
        // 并行获取海关编码和国家列表
        const [codesResponse, countriesResponse] = await Promise.all([
          dataAPI.getCustomsCodes(),
          dataAPI.getCountries()
        ]);
        setCustomsCodes(codesResponse);
        setCountries({
          import: countriesResponse.import_countries,
          export: countriesResponse.export_countries
        });
      } catch (error) {
        console.error('获取选项数据失败:', error);
        message.error('获取选项数据失败，请刷新页面重试');
      } finally {
        setLoading(false);
      }
    };

    fetchOptions();
  }, []);

  // 处理查询
  const handleSearch = async (values) => {
    try {
      setLoading(true);
      // 格式化查询参数
      const params = {
        ...values,
        page: pagination.current,
        page_size: pagination.pageSize,
        // 日期范围格式化
        start_date: values.date_range?.[0]?.format('YYYY-MM-DD'),
        end_date: values.date_range?.[1]?.format('YYYY-MM-DD'),
        // 移除date_range属性
        date_range: undefined
      };

      // 执行查询
      const response = await dataAPI.search(params);
      setDataSource(response.data);
      setPagination(prev => ({ ...prev, total: response.total, total_pages: response.total_pages }));
    } catch (error) {
      console.error('数据查询失败:', error);
      message.error('数据查询失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 处理重置
  // 处理导出功能
  const handleExport = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      // 构建导出参数，包含所有查询条件
      const exportParams = {
        ...values,
        start_date: values.date_range?.[0]?.format('YYYY-MM-DD'),
        end_date: values.date_range?.[1]?.format('YYYY-MM-DD'),
        date_range: undefined,
        // 导出所有数据，设置分页参数获取全部
        page: 1,
        page_size: pagination.total
      };

      // 调用API导出数据
      const response = await dataAPI.export(exportParams);
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `海关数据_${moment().format('YYYYMMDD')}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
      message.success('数据导出成功');
    } catch (error) {
      console.error('数据导出失败:', error);
      message.error('数据导出失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.resetFields();
  };

  // 处理分页变化
  const handleTableChange = (pagination, filters, sorter) => {
    setPagination(pagination);
    // 获取当前表单值并重新查询
    form.validateFields().then(values => {
      handleSearch({
      ...values,
      sort_by: sorter.field || '日期',
      sort_order: sorter.order === 'ascend' ? 'asc' : 'desc',
      page: pagination.current,
      page_size: pagination.pageSize
    });
    });
  };

  // 表格列定义
  const columns = [
    {
      title: '海关编码',
      dataIndex: '海关编码',
      key: '海关编码',
      sorter: true,
      width: 120
    },
    {
      title: '编码产品描述',
      dataIndex: '编码产品描述',
      key: '编码产品描述',
      sorter: true,
      width: 180
    },
    {
      title: '日期',
      dataIndex: '日期',
      key: '日期',
      sorter: true,
      width: 120
    },
    {
      title: '进口公司',
      dataIndex: '进口商',
      key: '进口商',
      sorter: true,
      width: 150
    },
    {
      title: '进口国家',
      dataIndex: '进口商所在国家',
      key: '进口商所在国家',
      sorter: true,
      width: 120
    },
    {
      title: '出口公司',
      dataIndex: '出口商',
      key: '出口商',
      sorter: true,
      width: 150
    },
    {
      title: '出口国家',
      dataIndex: '出口商所在国家',
      key: '出口商所在国家',
      sorter: true,
      width: 120
    },
    {
      title: '数量单位',
      dataIndex: '数量单位',
      key: '数量单位',
      sorter: true,
      width: 100
    },
    {
      title: '数量',
      dataIndex: '数量',
      key: '数量',
      sorter: true,
      width: 100,
      render: (text) => text?.toFixed(2)
    },
    {
      title: '公吨',
      dataIndex: '公吨',
      key: '公吨',
      sorter: true,
      width: 100,
      render: (text) => text?.toFixed(4)
    },
    {
      title: '金额美元',
      dataIndex: '金额美元',
      key: '金额美元',
      sorter: true,
      width: 120,
      render: (text) => `$${text?.toFixed(2)}`
    },
    {
      title: '详细产品名称',
      dataIndex: '详细产品名称',
      key: '详细产品名称',
      sorter: true,
      width: 200
    },
    {
      title: '提单号',
      dataIndex: '提单号',
      key: '提单号',
      sorter: true,
      width: 150
    },
    {
      title: '数据来源',
      dataIndex: '数据来源',
      key: '数据来源',
      sorter: true,
      width: 120
    },
    {
      title: '关单号',
      dataIndex: '关单号',
      key: '关单号',
      sorter: true,
      width: 150
    }
  ];

  return (
    <div className="data-query-page">
      <Title level={2}>海关数据查询</Title>
      <Card className="search-card">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSearch}
          initialValues={{ sort_by: '日期', sort_order: 'desc' }}
          className="query-form"
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={8} lg={6} xl={4}>
              <Form.Item name="海关编码" label="海关编码">
                <Select
                  showSearch
                  placeholder="选择或输入海关编码"
                  style={{ width: '100%' }}
                  filterOption={(input, option) =>
                    (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {customsCodes.map(code => (
                    <Option key={code} value={code}>{code}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8} lg={6} xl={4}>
              <Form.Item name="import_country" label="进口国家">
                <Select
                  showSearch
                  placeholder="选择进口国家"
                  style={{ width: '100%' }}
                  filterOption={(input, option) =>
                    (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {countries.import.map(country => (
                    <Option key={country} value={country}>{country}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8} lg={6} xl={4}>
              <Form.Item name="export_country" label="出口国家">
                <Select
                  showSearch
                  placeholder="选择出口国家"
                  style={{ width: '100%' }}
                  filterOption={(input, option) =>
                    (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {countries.export.map(country => (
                    <Option key={country} value={country}>{country}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={24} md={16} lg={12} xl={8}>
              <Form.Item name="date_range" label="日期范围">
                <RangePicker
                  format="YYYY-MM-DD"
                  style={{ width: '100%' }}
                  placeholder={['开始日期', '结束日期']}
                />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8} lg={6} xl={4}>
              <Form.Item name="importer" label="进口商">
                <Input placeholder="输入进口商名称" style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8} lg={6} xl={4}>
              <Form.Item name="exporter" label="出口商">
                <Input placeholder="输入出口商名称" style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={24} md={24} lg={24} xl={24} style={{ textAlign: 'right' }}>
              <Space size="middle">
                <Button type="primary" htmlType="submit" icon={<SearchOutlined />} loading={loading} size="middle">
                  查询
                </Button>
                <Button icon={<ReloadOutlined />} onClick={handleReset} size="middle">
                  重置
                </Button>
                <Button icon={<DownloadOutlined />} disabled={dataSource.length === 0} size="middle" onClick={handleExport}>
                  导出
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>
      </Card>

      <Card className="result-card" style={{ marginTop: 16 }}>
        <Spin spinning={loading} tip="数据加载中...">
          <Table
            columns={columns}
            dataSource={dataSource.map((item, index) => ({ ...item, key: index }))}
            pagination={pagination}
            onChange={handleTableChange}
            size="middle"
            bordered
            scroll={{ x: 'max-content' }}
          />
        </Spin>
      </Card>
    </div>
  );
};

export default DataQuery;