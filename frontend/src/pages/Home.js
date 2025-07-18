import React, { useState, useEffect } from 'react';
import { Input, Select, Button, Space, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import { dataAPI } from '../utils/api';

const { Option } = Select;
const { Search } = Input;

const Home = () => {
  const [searchType, setSearchType] = useState('customs_code');
  const [searchValue, setSearchValue] = useState('');
  const [customsCodes, setCustomsCodes] = useState([]);
  const [importCountries, setImportCountries] = useState([]);
  const [exportCountries, setExportCountries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const navigate = useNavigate();

  // 获取搜索选项数据
  useEffect(() => {
    const fetchOptions = async () => {
      try {
        setLoading(true);
        const [codesResponse, countriesResponse] = await Promise.all([
          dataAPI.getCustomsCodes(),
          dataAPI.getCountries()
        ]);
        setCustomsCodes(codesResponse);
        setImportCountries(countriesResponse.import_countries);
        setExportCountries(countriesResponse.export_countries);
      } catch (error) {
        console.error('获取搜索选项失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchOptions();
  }, []);

  const handleSearch = async () => {
    if (!searchValue.trim()) return;

  if (searchType === 'ai') {
    try {
      setAiLoading(true);
      // 调用DeepSeek API将自然语言转换为查询条件
      const response = await dataAPI.aiSearch(searchValue, exportCountries, importCountries)
        
        navigate('/data-query', { state: response });
      } catch (error) {
        console.error('AI搜索错误:', error);
        alert('AI搜索失败，请重试');
      } finally {
        setAiLoading(false);
      }
    } else {
      // 普通搜索类型直接跳转并传递参数
      const queryParams = {};
      switch(searchType) {
        case 'customs_code':
          queryParams.customs_code = searchValue;
          break;
        case 'export_country':
          queryParams.export_country = searchValue;
          break;
        case 'import_country':
          queryParams.import_country = searchValue;
          break;
        default:
          break;
      }
      navigate('/data-query', { state: queryParams });
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '80vh',
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '800px',
        textAlign: 'center'
      }}>
        <h1 style={{ marginBottom: '30px', color: '#1890ff' }}>海关数据查询系统</h1>
        <Space.Compact>
        <Select
            value={searchType}
            onChange={setSearchType}
            style={{ height: 40,width: 120 }}
          >
            <Option value="customs_code">海关编码</Option>
            <Option value="export_country">出口国家</Option>
            <Option value="import_country">进口国家</Option>
            <Option value="ai">AI搜索</Option>
          </Select>
          {searchType === 'ai' ?<Input
            // addonBefore={selectBefore}
            placeholder="请输入搜索内容..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: "360px" }}
            // enterButton="搜索"
            size="large"
            loading={aiLoading}
            />:<Select
                  showSearch
                  value={searchValue}
                  onChange={setSearchValue}
                  placeholder="请输入搜索内容..."
                  style={{ width: "360px" }}
                  filterOption={(input, option) =>
                    (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  dropdownStyle={{ maxHeight: 300, overflow: 'auto' }}
                  loading={loading}
                  size="large"
                >
                  {searchType === 'customs_code'
                    ? customsCodes.map(code => <Option key={code} value={code}>{code}</Option>)
                    : searchType === 'export_country'
                      ? exportCountries.map(country => <Option key={country} value={country}>{country}</Option>)
                      : searchType === 'import_country'
                        ? importCountries.map(country => <Option key={country} value={country}>{country}</Option>)
                        : null
                  }
                </Select>}
            <Button type="primary" size="large" onClick={handleSearch} loading={aiLoading}>
              搜索
            </Button>
              </Space.Compact>
      </div>
    </div>
  );
};

export default Home;