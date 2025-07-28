import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Layout, 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Button, 
  Input, 
  Select, 
  Space, 
  Typography, 
  Divider,
  Progress,
  Tag,
  Timeline,
  Avatar,
  Carousel,
  Form,
  DatePicker,
  AutoComplete,
  message
} from 'antd';
import { 
  SearchOutlined, 
  BarChartOutlined, 
  GlobalOutlined, 
  DatabaseOutlined,
  RiseOutlined,
  FileTextOutlined,
  DownloadOutlined,
  ApiOutlined,
  RightOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  LineChartOutlined,
  FundOutlined,
  ExportOutlined,
  ImportOutlined,
  LeftOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { dataAPI } from '../utils/api';
import './NewHome.css';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const NewHome = () => {
  // 原有的简单搜索状态（保留用于AI搜索）
  const [searchType, setSearchType] = useState('customs_code');
  const [searchValue, setSearchValue] = useState('');
  
  // 新的搜索表单状态
  const [form] = Form.useForm();
  const [searchFormData, setSearchFormData] = useState({
    customs_code: '',
    import_country: '',
    export_country: '',
    date_range: null,
    importer: '',
    exporter: ''
  });
  
  // 模糊查询相关状态
  const [fuzzySearch, setFuzzySearch] = useState({
    importer: true,
    exporter: true
  });
  
  // 建议相关状态
  const [suggestions, setSuggestions] = useState({
    importers: [],
    exporters: []
  });
  
  const [customsCodes, setCustomsCodes] = useState([]);
  const [importCountries, setImportCountries] = useState([]);
  const [exportCountries, setExportCountries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    totalRecords: 0,
    countries: 0,
    customsCodes: 0,
    lastUpdate: null
  });
  
  // 时间线相关状态
  const [timelineIndex, setTimelineIndex] = useState(0);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);
  const timelineRef = useRef(null);
  
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  // 轮播图工具数据 - 重新设计为图片为主
  const carouselTools = [
    {
      title: '海关数据查询平台',
      description: '全面的海关数据查询和分析工具，支持多维度数据检索和可视化展示',
      image: '/images/海关数据查询平台.png',
      url: '/data-query',
      buttonText: '开始查询'
    },
    {
      title: '贸易流向可视化',
      description: '直观展示全球贸易流向和商品流通路径，帮助理解国际贸易格局',
      image: '/images/贸易流转图工具.png',
      url: 'https://iie-customs.wandrop.com/#/customs',
      buttonText: '查看可视化'
    },
    {
      title: '数据分析工具',
      description: '深度分析全球贸易数据，发现商业机会和市场趋势',
      image: '/images/海关数据查询平台.png', // 复用图片
      url: 'https://comtradeplus.un.org/',
      buttonText: '立即使用'
    }
  ];

  // 时间线新闻数据 - 扩展更多历史事件
  const timelineNews = [
    {
      date: '2024-01-15',
      type: 'feature',
      tag: { color: 'blue', text: '功能更新' },
      title: '新增AI智能搜索功能',
      content: '平台新增AI智能搜索功能，支持自然语言查询，让数据检索更加便捷高效。',
      featured: true
    },
    {
      date: '2024-01-10',
      type: 'data',
      tag: { color: 'green', text: '数据更新' },
      title: '2023年度贸易数据发布',
      content: '2023年全球贸易统计数据已完成整理并正式发布，涵盖全球主要经济体贸易数据。',
      featured: false
    },
    {
      date: '2024-01-05',
      type: 'system',
      tag: { color: 'purple', text: '系统公告' },
      title: '系统维护通知',
      content: '为提升用户体验，系统将于本周末进行例行维护升级，预计维护时间2小时。',
      featured: false
    },
    {
      date: '2023-12-20',
      type: 'feature',
      tag: { color: 'blue', text: '功能更新' },
      title: '新增数据可视化图表',
      content: '平台新增多种数据可视化图表类型，包括热力图、桑基图等，提升数据分析体验。',
      featured: false
    },
    {
      date: '2023-12-15',
      type: 'data',
      tag: { color: 'green', text: '数据更新' },
      title: '新增东南亚贸易数据',
      content: '平台新增东南亚地区详细贸易数据，覆盖ASEAN十国的进出口统计信息。',
      featured: false
    },
    {
      date: '2023-12-01',
      type: 'feature',
      tag: { color: 'orange', text: '性能优化' },
      title: '查询性能大幅提升',
      content: '通过数据库优化和缓存机制改进，数据查询速度提升300%，用户体验显著改善。',
      featured: true
    },
    {
      date: '2023-11-20',
      type: 'system',
      tag: { color: 'red', text: '重要公告' },
      title: '用户权限系统升级',
      content: '用户权限管理系统全面升级，新增角色管理和细粒度权限控制功能。',
      featured: false
    },
    {
      date: '2023-11-10',
      type: 'data',
      tag: { color: 'green', text: '数据更新' },
      title: '历史数据回溯至2000年',
      content: '平台历史数据回溯范围扩展至2000年，为长期趋势分析提供更丰富的数据支持。',
      featured: false
    }
  ];

  // 获取统计数据和搜索选项
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [codesResponse, countriesResponse] = await Promise.all([
          dataAPI.getCustomsCodes(),
          dataAPI.getCountries()
        ]);
        
        setCustomsCodes(codesResponse);
        setImportCountries(countriesResponse.import_countries);
        setExportCountries(countriesResponse.export_countries);
        
        // 设置统计数据
        setStats({
          totalRecords: 2580000, // 示例数据
          countries: countriesResponse.import_countries.length + countriesResponse.export_countries.length,
          customsCodes: codesResponse.length,
          lastUpdate: new Date().toLocaleDateString()
        });
      } catch (error) {
        console.error('获取数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // 时间线滚动功能
  const scrollTimeline = (direction) => {
    const itemWidth = 390; // 350px + 40px gap
    const maxIndex = Math.max(0, timelineNews.length - 3); // 显示3个项目
    
    let newIndex = timelineIndex;
    if (direction === 'left' && timelineIndex > 0) {
      newIndex = timelineIndex - 1;
    } else if (direction === 'right' && timelineIndex < maxIndex) {
      newIndex = timelineIndex + 1;
    }
    
    setTimelineIndex(newIndex);
    
    if (timelineRef.current) {
      const scrollLeft = newIndex * itemWidth;
      timelineRef.current.style.transform = `translateX(-${scrollLeft}px)`;
    }
    
    updateTimelineButtons(newIndex);
  };

  const updateTimelineButtons = useCallback((index) => {
    const maxIndex = Math.max(0, timelineNews.length - 3);
    setCanScrollLeft(index > 0);
    setCanScrollRight(index < maxIndex);
  }, [timelineNews.length]);

  // 组件挂载后初始化按钮状态
  useEffect(() => {
    updateTimelineButtons(0);
  }, [updateTimelineButtons]);

  // 处理进口商搜索建议
  const handleImporterSearch = async (value) => {
    if (value && value.length > 1) {
      try {
        const response = await dataAPI.getImportersSuggestions(value);
        setSuggestions(prev => ({ ...prev, importers: response || [] }));
      } catch (error) {
        console.error('获取进口商建议失败:', error);
        setSuggestions(prev => ({ ...prev, importers: [] }));
      }
    } else {
      setSuggestions(prev => ({ ...prev, importers: [] }));
    }
  };

  // 处理出口商搜索建议
  const handleExporterSearch = async (value) => {
    if (value && value.length > 1) {
      try {
        const response = await dataAPI.getExportersSuggestions(value);
        setSuggestions(prev => ({ ...prev, exporters: response || [] }));
      } catch (error) {
        console.error('获取出口商建议失败:', error);
        setSuggestions(prev => ({ ...prev, exporters: [] }));
      }
    } else {
      setSuggestions(prev => ({ ...prev, exporters: [] }));
    }
  };

  // 处理高级搜索表单提交
  const handleAdvancedSearch = async (values) => {
    // 检查是否已登录，未登录则跳转到登录页面
    if (!isAuthenticated) {
      navigate('/login', { 
        state: { 
          from: { pathname: '/data-query' },
          message: '请先登录以使用数据查询功能'
        }
      });
      return;
    }

    try {
      // 格式化查询参数
      const params = {
        ...values,
        // 日期范围格式化
        start_date: values.date_range?.[0]?.format('YYYY-MM-DD'),
        end_date: values.date_range?.[1]?.format('YYYY-MM-DD'),
        // 添加模糊查询参数
        fuzzy_importer: fuzzySearch.importer,
        fuzzy_exporter: fuzzySearch.exporter,
        // 移除date_range属性
        date_range: undefined
      };

      // 跳转到数据查询页面并传递参数
      navigate('/data-query', { state: params });
    } catch (error) {
      console.error('搜索参数处理失败:', error);
      message.error('搜索参数处理失败，请重试');
    }
  };

  // 处理表单重置
  const handleReset = () => {
    form.resetFields();
    // 重置模糊搜索状态为默认开启
    setFuzzySearch({
      importer: true,
      exporter: true
    });
    // 清空建议
    setSuggestions({
      importers: [],
      exporters: []
    });
  };

  // 处理未登录状态下的搜索按钮点击
  const handleLoginPrompt = () => {
    navigate('/login', { 
      state: { 
        from: { pathname: '/data-query' },
        message: '请先登录以使用数据查询功能'
      }
    });
  };

  // 处理轮播图工具点击
  const handleToolClick = (tool) => {
    if (tool.url.startsWith('http')) {
      // 外部链接，新窗口打开
      window.open(tool.url, '_blank');
    } else {
      // 内部路由，检查是否需要登录
      if (!isAuthenticated && tool.url !== '/new-home') {
        navigate('/login', { 
          state: { 
            from: { pathname: tool.url },
            message: '请先登录以使用此功能'
          }
        });
        return;
      }
      navigate(tool.url);
    }
  };

  // 处理功能特性卡片点击
  const handleFeatureClick = (feature) => {
    // 检查是否需要登录
    if (!isAuthenticated && feature.link !== '/new-home') {
      navigate('/login', { 
        state: { 
          from: { pathname: feature.link },
          message: '请先登录以使用此功能'
        }
      });
      return;
    }
    navigate(feature.link);
  };

  const features = [
    {
      icon: <DatabaseOutlined style={{ fontSize: '48px', color: '#1890ff' }} />,
      title: '全球贸易数据',
      description: '覆盖全球200多个国家和地区的详细贸易统计数据，包含年度和月度贸易统计信息。',
      link: '/data-query'
    },
    {
      icon: <BarChartOutlined style={{ fontSize: '48px', color: '#52c41a' }} />,
      title: '数据可视化',
      description: '提供多种图表和可视化工具，帮助您更好地理解和分析贸易数据趋势。',
      link: '/data-query'
    },
    {
      icon: <ApiOutlined style={{ fontSize: '48px', color: '#722ed1' }} />,
      title: 'API 接口',
      description: '为开发者提供RESTful API接口，支持将贸易数据集成到企业应用和工作流中。',
      link: '/config-management'
    },
    {
      icon: <FileTextOutlined style={{ fontSize: '48px', color: '#fa8c16' }} />,
      title: '数据导入',
      description: '支持批量数据导入功能，可以导入Excel、CSV等格式的贸易数据文件。',
      link: '/import'
    }
  ];

  const dataAvailability = [
    { stage: '已注册', count: 1250, color: '#1890ff' },
    { stage: '处理中', count: 320, color: '#faad14' },
    { stage: '审核中', count: 180, color: '#722ed1' },
    { stage: '已发布', count: 2100, color: '#52c41a' }
  ];

  return (
    <div className="new-home-content">
      <Layout 
        className="new-home-layout"
        style={{ 
          background: `url('/images/background.jpeg') center/cover no-repeat fixed`,
          minHeight: '100vh',
          position: 'relative'
        }}
      >
        {/* 背景遮罩层 */}
        {/* <div className="background-overlay" /> */}
        
        {/* 内容区域 */}
        <div className="content-wrapper">
          {/* 英雄区域 */}
          <div className="hero-section">
            <div className="hero-container">
              <Title level={1} className="hero-title">
                海关数据平台
              </Title>
              <Paragraph className="hero-description">
                全球最全面的海关贸易数据平台。联合国统计司汇总的详细全球年度和月度贸易统计数据，
                涵盖约200个国家，代表全球99%以上的商品贸易。
              </Paragraph>
              
              {/* 搜索区域 */}
              <div className="search-container">
                {!isAuthenticated ? (
                  // 未登录状态：显示"开始搜索"按钮
                  <div style={{ textAlign: 'center' }}>
                    <Button 
                      type="primary" 
                      size="large" 
                      icon={<SearchOutlined />}
                      onClick={handleLoginPrompt}
                      className="search-button"
                      style={{ 
                        fontSize: '18px', 
                        height: '60px', 
                        padding: '0 40px',
                        borderRadius: '30px'
                      }}
                    >
                      开始搜索
                    </Button>
                    <div style={{ marginTop: '16px', color: 'rgba(255, 255, 255, 0.8)' }}>
                      登录后可使用完整的数据查询功能
                    </div>
                  </div>
                ) : (
                  // 已登录状态：显示完整搜索表单
                  <Card 
                    style={{ 
                      background: 'rgba(255, 255, 255, 0.95)', 
                      backdropFilter: 'blur(10px)',
                      borderRadius: '16px',
                      border: 'none',
                      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                    }}
                  >
                    <Form
                      form={form}
                      layout="vertical"
                      onFinish={handleAdvancedSearch}
                      style={{ margin: 0 }}
                    >
                      <Row gutter={[16, 16]}>
                        <Col xs={24} sm={12} md={8}>
                          <Form.Item name="customs_code" label="海关编码" style={{ marginBottom: '16px' }}>
                            <Select
                              showSearch
                              allowClear
                              placeholder="选择或输入海关编码"
                              style={{ width: '100%' }}
                              filterOption={(input, option) =>
                                (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                              }
                              size="large"
                            >
                              {(customsCodes || []).map(code => (
                                <Option key={code} value={code}>{code}</Option>
                              ))}
                            </Select>
                          </Form.Item>
                        </Col>

                        <Col xs={24} sm={12} md={8}>
                          <Form.Item name="import_country" label="进口国家" style={{ marginBottom: '16px' }}>
                            <Select
                              showSearch
                              allowClear
                              placeholder="选择进口国家"
                              style={{ width: '100%' }}
                              filterOption={(input, option) =>
                                (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                              }
                              size="large"
                            >
                              {(importCountries || []).map(country => (
                                <Option key={country} value={country}>{country}</Option>
                              ))}
                            </Select>
                          </Form.Item>
                        </Col>

                        <Col xs={24} sm={12} md={8}>
                          <Form.Item name="export_country" label="出口国家" style={{ marginBottom: '16px' }}>
                            <Select
                              showSearch
                              allowClear
                              placeholder="选择出口国家"
                              style={{ width: '100%' }}
                              filterOption={(input, option) =>
                                (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                              }
                              size="large"
                            >
                              {(exportCountries || []).map(country => (
                                <Option key={country} value={country}>{country}</Option>
                              ))}
                            </Select>
                          </Form.Item>
                        </Col>

                        <Col xs={24} sm={12} md={8}>
                          <Form.Item name="date_range" label="日期范围" style={{ marginBottom: '16px' }}>
                            <RangePicker
                              format="YYYY-MM-DD"
                              style={{ width: '100%' }}
                              placeholder={['开始日期', '结束日期']}
                              size="large"
                            />
                          </Form.Item>
                        </Col>

                        <Col xs={24} sm={12} md={8}>
                          <Form.Item name="importer" label="进口商" style={{ marginBottom: '16px' }}>
                            <div style={{ display: 'flex', gap: '8px' }}>
                              <AutoComplete
                                style={{ flex: 1 }}
                                placeholder="输入进口商名称"
                                onSearch={handleImporterSearch}
                                options={(suggestions.importers || []).map(item => ({ value: item }))}
                                filterOption={false}
                                allowClear
                                size="large"
                              />
                              <Button 
                                type={fuzzySearch.importer ? "primary" : "default"}
                                onClick={() => setFuzzySearch(prev => ({ ...prev, importer: !prev.importer }))}
                                size="large"
                              >
                                模糊
                              </Button>
                            </div>
                          </Form.Item>
                        </Col>

                        <Col xs={24} sm={12} md={8}>
                          <Form.Item name="exporter" label="出口商" style={{ marginBottom: '16px' }}>
                            <div style={{ display: 'flex', gap: '8px' }}>
                              <AutoComplete
                                style={{ flex: 1 }}
                                placeholder="输入出口商名称"
                                onSearch={handleExporterSearch}
                                options={(suggestions.exporters || []).map(item => ({ value: item }))}
                                filterOption={false}
                                allowClear
                                size="large"
                              />
                              <Button 
                                type={fuzzySearch.exporter ? "primary" : "default"}
                                onClick={() => setFuzzySearch(prev => ({ ...prev, exporter: !prev.exporter }))}
                                size="large"
                              >
                                模糊
                              </Button>
                            </div>
                          </Form.Item>
                        </Col>

                        <Col xs={24} style={{ textAlign: 'center', marginTop: '8px' }}>
                          <Space size="middle">
                            <Button 
                              type="primary" 
                              htmlType="submit" 
                              icon={<SearchOutlined />} 
                              loading={loading} 
                              size="large"
                              style={{ minWidth: '120px' }}
                            >
                              查询
                            </Button>
                            <Button 
                              icon={<ReloadOutlined />} 
                              onClick={handleReset} 
                              size="large"
                              style={{ minWidth: '120px' }}
                            >
                              重置
                            </Button>
                          </Space>
                        </Col>
                      </Row>
                    </Form>
                  </Card>
                )}
              </div>
            </div>
          </div>

          {/* 工具轮播图区域 - 重新设计 */}
          <div className="carousel-section">
            <div className="carousel-container">
              <div className="carousel-header">
                <Title level={2}>专业工具</Title>
                <Paragraph className="carousel-description">
                  探索我们的专业贸易分析工具，助力您的商业决策
                </Paragraph>
              </div>   
              
              <Carousel 
                autoplay 
                arrows
                className="custom-carousel"
              >
                {carouselTools.map((tool, index) => (
                  <div key={index}>
                    <div className="carousel-slide">
                      <img 
                        src={tool.image} 
                        alt={tool.title} 
                        className="carousel-image"
                      />
                      <div className="carousel-content">
                        <Title level={2} className="carousel-title">
                          {tool.title}
                        </Title>
                        <Paragraph className="carousel-description-text">
                          {tool.description}
                        </Paragraph>
                        <Button 
                          type="primary" 
                          size="large"
                          icon={<ExportOutlined />}
                          onClick={() => handleToolClick(tool)}
                          className="carousel-button"
                        >
                          {tool.buttonText}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </Carousel>
            </div>
          </div>

          {/* 统计数据区域 */}
          <div className="stats-section">
            <div className="stats-container">
              <Row gutter={[32, 32]}>
                <Col xs={24} sm={12} md={6}>
                  <Card className="stats-card">
                    <Statistic
                      title="总记录数"
                      value={stats.totalRecords}
                      prefix={<DatabaseOutlined />}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card className="stats-card">
                    <Statistic
                      title="覆盖国家"
                      value={stats.countries}
                      prefix={<GlobalOutlined />}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card className="stats-card">
                    <Statistic
                      title="海关编码"
                      value={stats.customsCodes}
                      prefix={<FileTextOutlined />}
                      valueStyle={{ color: '#722ed1' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card className="stats-card">
                    <div className="last-update-card">
                      <Text type="secondary">最后更新</Text>
                    </div>
                    <div className="last-update-text">
                      {stats.lastUpdate}
                    </div>
                  </Card>
                </Col>
              </Row>
            </div>
          </div>

          {/* 功能特性区域 */}
          <div className="features-section">
            <div className="features-container">
              <div className="features-header">
                <Title level={2}>平台功能</Title>
                <Paragraph className="features-description">
                  为政府、学术机构、研究所和企业提供全面的贸易数据分析工具
                </Paragraph>
              </div>
              
              <Row gutter={[32, 32]}>
                {features.map((feature, index) => (
                  <Col xs={24} sm={12} md={6} key={index}>
                    <Card 
                      hoverable
                      className="feature-card"
                      bodyStyle={{ padding: '32px 24px' }}
                      onClick={() => handleFeatureClick(feature)}
                    >
                      <div className="feature-icon">
                        {feature.icon}
                      </div>
                      <Title level={4} className="feature-title">
                        {feature.title}
                      </Title>
                      <Paragraph className="feature-description">
                        {feature.description}
                      </Paragraph>
                      <Button type="link" icon={<RightOutlined />}>
                        了解更多
                      </Button>
                    </Card>
                  </Col>
                ))}
              </Row>
            </div>
          </div>

          {/* 数据可用性趋势 */}
          <div className="availability-section">
            <div className="availability-container">
              <Row gutter={[48, 48]} align="middle">
                <Col xs={24} lg={12}>
                  <Title level={2}>数据可用性</Title>
                  <Paragraph className="availability-description">
                    官方贸易数据持续收集并向公众发布。可用性趋势显示了数据集在从注册到发布的数据处理流水线中各个阶段的数量分布。
                  </Paragraph>
                  
                  <div style={{ marginBottom: '24px' }}>
                    {dataAvailability.map((item, index) => (
                      <div key={index} className="availability-item">
                        <div className="availability-item-header">
                          <Text strong>{item.stage}</Text>
                          <Text>{item.count.toLocaleString()}</Text>
                        </div>
                        <Progress 
                          percent={(item.count / 3850) * 100} 
                          strokeColor={item.color}
                          showInfo={false}
                        />
                      </div>
                    ))}
                  </div>
                  
                  <Space>
                    <Button type="primary" icon={<BarChartOutlined />}>
                      查看详细统计
                    </Button>
                    <Button icon={<DownloadOutlined />}>
                      下载报告
                    </Button>
                  </Space>
                </Col>
                
                <Col xs={24} lg={12}>
                  <div className="chart-placeholder">
                    <RiseOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                    <div>数据趋势图表</div>
                  </div>
                </Col>
              </Row>
            </div>
          </div>

          {/* 最新动态 - 横向时间线 */}
          <div className="news-section">
            <div className="news-container">
              <div className="news-header">
                <Title level={2}>中美贸易战信息</Title>
                <Paragraph className="news-description">
                  了解平台最新功能更新和重要公告
                </Paragraph>
              </div>
              
              {/* 横向时间线 */}
              <div className="news-timeline-wrapper">
                <div className="news-timeline-nav">
                  <button 
                    className="timeline-nav-button"
                    onClick={() => scrollTimeline('left')}
                    disabled={!canScrollLeft}
                  >
                    <LeftOutlined />
                  </button>
                  
                  <div className="news-timeline-container">
                    <div className="news-timeline" ref={timelineRef}>
                      {timelineNews.map((news, index) => (
                        <div key={index} className="timeline-item">
                          <div className="timeline-date">{news.date}</div>
                          <div className={`timeline-node ${news.featured ? 'featured' : ''}`}></div>
                          <Card className="timeline-card">
                            <div className="news-meta">
                              <Tag color={news.tag.color}>{news.tag.text}</Tag>
                            </div>
                            <Title level={4} className="news-title">
                              {news.title}
                            </Title>
                            <Paragraph className="news-content">
                              {news.content}
                            </Paragraph>
                            <Button type="link" icon={<RightOutlined />}>
                              查看详情
                            </Button>
                          </Card>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <button 
                    className="timeline-nav-button"
                    onClick={() => scrollTimeline('right')}
                    disabled={!canScrollRight}
                  >
                    <RightOutlined />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 快速访问 */}
          <div className="quick-access-section">
            <div className="quick-access-container">
              <div className="quick-access-header">
                <Title level={2}>快速访问</Title>
                <Paragraph className="quick-access-description">
                  常用功能快速入口，提升您的工作效率
                </Paragraph>
              </div>
              
              <Row gutter={[24, 24]}>
                <Col xs={24} sm={12} md={6}>
                  <Card 
                    hoverable
                    className="quick-access-card"
                    bodyStyle={{ padding: '40px 24px' }}
                    onClick={() => navigate('/data-query')}
                  >
                    <div className="quick-access-icon">
                      <SearchOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
                    </div>
                    <Title level={4} className="quick-access-title">
                      数据查询
                    </Title>
                    <Paragraph className="quick-access-description-text">
                      快速查询海关贸易数据
                    </Paragraph>
                  </Card>
                </Col>
                
                <Col xs={24} sm={12} md={6}>
                  <Card 
                    hoverable
                    className="quick-access-card"
                    bodyStyle={{ padding: '40px 24px' }}
                    onClick={() => navigate('/import')}
                  >
                    <div className="quick-access-icon">
                      <ImportOutlined style={{ fontSize: '48px', color: '#52c41a' }} />
                    </div>
                    <Title level={4} className="quick-access-title">
                      数据导入
                    </Title>
                    <Paragraph className="quick-access-description-text">
                      批量导入贸易数据文件
                    </Paragraph>
                  </Card>
                </Col>
                
                <Col xs={24} sm={12} md={6}>
                  <Card 
                    hoverable
                    className="quick-access-card"
                    bodyStyle={{ padding: '40px 24px' }}
                    onClick={() => navigate('/user-management')}
                  >
                    <div className="quick-access-icon">
                      <DatabaseOutlined style={{ fontSize: '48px', color: '#722ed1' }} />
                    </div>
                    <Title level={4} className="quick-access-title">
                      用户管理
                    </Title>
                    <Paragraph className="quick-access-description-text">
                      管理系统用户和权限
                    </Paragraph>
                  </Card>
                </Col>
                
                <Col xs={24} sm={12} md={6}>
                  <Card 
                    hoverable
                    className="quick-access-card"
                    bodyStyle={{ padding: '40px 24px' }}
                    onClick={() => navigate('/config-management')}
                  >
                    <div className="quick-access-icon">
                      <ApiOutlined style={{ fontSize: '48px', color: '#fa8c16' }} />
                    </div>
                    <Title level={4} className="quick-access-title">
                      系统配置
                    </Title>
                    <Paragraph className="quick-access-description-text">
                      配置系统参数和设置
                    </Paragraph>
                  </Card>
                </Col>
              </Row>
            </div>
          </div>
        </div>
      </Layout>
    </div>
  );
};

export default NewHome;