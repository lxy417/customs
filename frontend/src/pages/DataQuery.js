import React, { useState, useEffect, useRef, useContext } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Form, Input, Select, DatePicker, Button, Table, Space, Typography, Card, Spin, message, Row, Col, Modal, AutoComplete } from 'antd';
import { SearchOutlined, ReloadOutlined, DownloadOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { dataAPI } from '../utils/api';
import { usePermissions, PERMISSIONS } from '../utils/permissions';
import moment from 'moment';
import * as XLSX from 'xlsx';
import './DataQuery.css';
moment.locale('zh-cn');

const { Title } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const DataQuery = () => {
  const [sorter, setSorter] = useState({});
  const location = useLocation();
  const { user } = useAuth();
  const { hasPermission } = usePermissions(user);
  const [countries, setCountries] = useState({ import: [], export: [] });
  const [form] = Form.useForm();
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [currentRecord, setCurrentRecord] = useState(null);
  const [editForm] = Form.useForm();
  const [dataSource, setDataSource] = useState([]);
  const [loading, setLoading] = useState(false);

  // 模糊查询相关状态 - 默认开启模糊搜索
  const [fuzzySearch, setFuzzySearch] = useState({
    importer: true,
    exporter: true
  });
  const [suggestions, setSuggestions] = useState({
    importers: [],
    exporters: []
  });

  // 从首页接收搜索参数并自动填充
  useEffect(() => {
      const searchParams = location.state;
      if (searchParams) {
        const formattedSearchParams = { ...searchParams };
        // 检查并转换日期范围
        if (formattedSearchParams.start_date && formattedSearchParams.end_date) {
          formattedSearchParams.date_range = [
            moment(formattedSearchParams.start_date),
            moment(formattedSearchParams.end_date)
          ];
          // 移除原始的 start_date 和 end_date 字段，因为 DatePicker 期望的是 date_range
          delete formattedSearchParams.start_date;
          delete formattedSearchParams.end_date;
        } else if (formattedSearchParams.start_date) {
          // 如果只有开始日期，也可以考虑单独处理或将其设为日期范围的开始
          formattedSearchParams.date_range = [moment(formattedSearchParams.start_date), null];
          delete formattedSearchParams.start_date;
        } else if (formattedSearchParams.end_date) {
          // 如果只有结束日期
          formattedSearchParams.date_range = [null, moment(formattedSearchParams.end_date)];
          delete formattedSearchParams.end_date;
        }

        form.setFieldsValue(formattedSearchParams);
        // 如果有参数则自动触发搜索
        handleSearch(form.getFieldsValue());
      }
  }, [location.state, form]);

  
  const [pagination, setPagination] = useState({
    total: 0,
    total_pages: 0,
    current: 1,
    pageSize: 20,
    showSizeChanger: true,
    showTotal: (total) => `共 ${total} 条记录，共 ${Math.ceil(total / pagination.pageSize)} 页`
  });
  const [customsCodes, setCustomsCodes] = useState([]);

  // --- 核心修改：在 useEffect 中使用 setFieldsValue 清空所有字段 ---
  useEffect(() => {
    if (editModalVisible) { // 只有当 Modal 显示时才操作表单
      if (currentRecord) { // 编辑模式：填充数据
        const formattedRecord = {
          ...currentRecord,
          // 确保日期是 moment 对象
          日期: currentRecord.日期 ? moment(currentRecord.日期) : null,
          // 如果其他字段也是字符串但DatePicker/Select期望其他类型，也在此处转换
        };
        editForm.setFieldsValue(formattedRecord);
      } else { // 新增模式：使用 setFieldsValue 清空所有字段
        editForm.setFieldsValue({
          海关编码: undefined, // 或 null / ''
          编码产品描述: undefined,
          日期: undefined, // 对于 DatePicker，undefined 或 null 是清空值
          进口商: undefined,
          进口商所在国家: undefined,
          出口商: undefined,
          出口商所在国家: undefined,
          数量单位: undefined,
          数量: undefined,
          公吨: undefined,
          金额美元: undefined,
          详细产品名称: undefined,
          提单号: undefined,
          数据来源: undefined,
          关单号: undefined,
          // 确保这里包含了所有表单中的字段名
        });
      }
    }
  }, [editModalVisible, currentRecord, editForm]); // 依赖 editForm 以确保其稳定

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
        setCustomsCodes(codesResponse || []);
        setCountries({
          import: countriesResponse?.import_countries || [],
          export: countriesResponse?.export_countries || []
        });
      } catch (error) {
        console.error('获取选项数据失败:', error);
        message.error('获取选项数据失败，请刷新页面重试');
        // 设置默认值以防止错误
        setCustomsCodes([]);
        setCountries({ import: [], export: [] });
      } finally {
        setLoading(false);
      }
    };

    fetchOptions();
  }, []);

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

  // 处理查询
  const handleSearch = async (values) => {
    try {
      setLoading(true);
      // 格式化查询参数
      const params = {
        ...values,
        page: values.page ? values.page : pagination.current,
        page_size: values.page_size ? values.page_size : pagination.pageSize,
        // 日期范围格式化
        start_date: values.date_range?.[0]?.format('YYYY-MM-DD'),
        end_date: values.date_range?.[1]?.format('YYYY-MM-DD'),
        // 添加模糊查询参数
        fuzzy_importer: fuzzySearch.importer,
        fuzzy_exporter: fuzzySearch.exporter,
        // 移除date_range属性
        date_range: undefined
      };

      // 执行查询
      const response = await dataAPI.searchData(params);
      setDataSource((response.data || []).map(item => ({ ...item, key: item.id })));
      setPagination(prev => ({ ...prev, total: response.total, total_pages: response.total_pages}));
    } catch (error) {
      console.error('数据查询失败:', error);
      message.error('数据查询失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 处理重置
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

  // 处理单个删除
  const handleDelete = async (id) => {
    if (window.confirm('确定要删除这条记录吗？')) {
      try {
        setLoading(true);
        await dataAPI.delete(id);
        message.success('删除成功');
        handleSearch(form.getFieldsValue()); // 重新查询
      } catch (error) {
        message.error('删除失败，请重试');
      } finally {
        setLoading(false);
      }
    }
  };

  // 处理批量删除当前查询结果
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleBulkDelete = () => {
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async (deleteAll) => {
    try {
      setLoading(true);
      if (deleteAll) {
        // 删除所有符合当前搜索条件的记录
        const formValues = form.getFieldsValue();
        // 使用与搜索相同的参数格式化逻辑
        const params = {
          ...formValues,
          // 日期范围格式化
          start_date: formValues.date_range?.[0]?.format('YYYY-MM-DD'),
          end_date: formValues.date_range?.[1]?.format('YYYY-MM-DD'),
          // 添加模糊查询参数
          fuzzy_importer: fuzzySearch.importer,
          fuzzy_exporter: fuzzySearch.exporter,
          // 移除date_range属性
          date_range: undefined
        };
        
        await dataAPI.bulkDeleteByCondition(params);
        message.success('所有符合条件的记录已删除');
      } else {
        // 删除当前显示的记录
        const ids = dataSource.map(item => item.id);
        await dataAPI.bulkDelete(ids);
        message.success(`已删除当前显示的 ${dataSource.length} 条记录`);
      }
      handleSearch(form.getFieldsValue()); // 重新查询
    } catch (error) {
      message.error('批量删除失败，请重试');
    } finally {
      setLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  // 处理编辑操作
  const handleEdit = (record) => {
    setCurrentRecord(record);
    // 关键修改：将日期字符串转换为 moment 对象
    const formattedRecord = {
      ...record,
      日期: record.日期 ? moment(record.日期) : null,
    };
    editForm.setFieldsValue(formattedRecord);
    setEditModalVisible(true);
  };

  // 处理保存编辑
  const handleSaveEdit = async () => {
    try {
      const values = await editForm.validateFields();
      setLoading(true);
      // 关键修改：将 moment 对象转换回 YYYY-MM-DD 字符串，以便发送给后端 API
      const formattedValues = {
          ...values,
          // 如果 values.日期 是 moment 对象，就用 format('YYYY-MM-DD') 转换
          // 否则，如果它已经是字符串（例如，在创建新记录时，如果 DatePicker 没有值），则保留原样
          日期: values.日期 ? moment(values.日期).format('YYYY-MM-DD') : null,
          // 确保其他可能需要格式化的字段也进行处理，例如金额、公吨等
          // 假设后端接受数字类型，确保这里发送的是数字
          数量: values.数量 ? parseFloat(values.数量) : null,
          公吨: values.公吨 ? parseFloat(values.公吨) : null,
          金额美元: values.金额美元 ? parseFloat(values.金额美元) : null,
        };
      if (currentRecord) {
        // 更新现有记录
        await dataAPI.update(currentRecord.id, formattedValues);
        message.success('更新成功');
      } else {
        // 创建新记录
        await dataAPI.create(formattedValues);
        message.success('创建成功');
      }
      setEditModalVisible(false);
      handleSearch({
        ...form.getFieldsValue(),
        page: pagination.current,
        page_size: pagination.pageSize,
      });
    } catch (error) {
      message.error(currentRecord ? '更新失败' : '创建失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理导出功能
  const handleExport = async () => {
    try {
      setLoading(true);
      const values = form.getFieldsValue();
      // 构建导出参数，使用与搜索相同的参数格式化逻辑
      const exportParams = {
        ...values,
        // 日期范围格式化
        start_date: values.date_range?.[0]?.format('YYYY-MM-DD'),
        end_date: values.date_range?.[1]?.format('YYYY-MM-DD'),
        // 添加模糊查询参数
        fuzzy_importer: fuzzySearch.importer,
        fuzzy_exporter: fuzzySearch.exporter,
        // 移除date_range属性
        date_range: undefined,
        // 添加排序参数（导出时不需要分页参数）
        sort_by: sorter.field || '日期',
        sort_order: sorter.order === 'ascend' ? 'asc' : 'desc'
      };

      // 调用API导出数据
      const response = await dataAPI.export(exportParams);
      const jsonData = response.data;

      if (!jsonData || jsonData.length === 0) {
        throw Error('没有可导出的数据');
      }
      // --- 使用 xlsx 库将 JSON 转换为 Excel ---
      const ws = XLSX.utils.json_to_sheet(jsonData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, '海关数据'); // '海关数据' 是工作表的名称

      // 生成 Excel 文件的二进制数据
      // type: 'array' 会返回一个 Uint8Array，这更适合创建 Blob
      const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });

      const blob = new Blob([excelBuffer], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `贸易数据_${moment().format('YYYYMMDD')}.xlsx`;
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

  // 处理分页变化
  const handleTableChange = (paginations, filters, sorter) => {
    setPagination(prev => ({...prev, ...paginations}))
    setSorter(sorter);
    
    // 处理筛选器
    const filterParams = {};
    Object.keys(filters).forEach(key => {
      if (filters[key] && filters[key].length > 0) {
        filterParams[`filter_${key}`] = filters[key];
      }
    });
    
    // 获取当前表单值并重新查询
    form.validateFields().then(values => {
      handleSearch({
        ...values,
        ...filterParams,
        sort_by: sorter.field || '日期',
        sort_order: sorter.order === 'ascend' ? 'asc' : 'desc',
        page: paginations.current,
        page_size: paginations.pageSize
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
      width: 120,
      fixed: 'left',
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索海关编码"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => record['海关编码']?.toString().toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '编码产品描述',
      dataIndex: '编码产品描述',
      key: '编码产品描述',
      sorter: true,
      width: 180,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索产品描述"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => record['编码产品描述']?.toString().toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '日期',
      dataIndex: '日期',
      key: '日期',
      sorter: true,
      width: 120,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <RangePicker
            value={selectedKeys[0] ? [moment(selectedKeys[0][0]), moment(selectedKeys[0][1])] : []}
            onChange={dates => setSelectedKeys(dates ? [dates.map(d => d?.format('YYYY-MM-DD'))] : [])}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => {
        if (!value || !value[0] || !value[1]) return true;
        const recordDate = moment(record['日期']);
        return recordDate.isBetween(moment(value[0]), moment(value[1]), 'day', '[]');
      },
    },
    {
      title: '进口商',
      dataIndex: '进口商',
      key: '进口商',
      sorter: true,
      width: 150,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索进口商"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => record['进口商']?.toString().toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '进口国家',
      dataIndex: '进口商所在国家',
      key: '进口商所在国家',
      sorter: true,
      width: 120,
      filters: countries.import?.map(country => ({ text: country, value: country })) || [],
      onFilter: (value, record) => record['进口商所在国家'] === value,
    },
    {
      title: '出口商',
      dataIndex: '出口商',
      key: '出口商',
      sorter: true,
      width: 150,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索出口商"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => record['出口商']?.toString().toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '出口国家',
      dataIndex: '出口商所在国家',
      key: '出口商所在国家',
      sorter: true,
      width: 120,
      filters: countries.export?.map(country => ({ text: country, value: country })) || [],
      onFilter: (value, record) => record['出口商所在国家'] === value,
    },
    {
      title: '数量单位',
      dataIndex: '数量单位',
      key: '数量单位',
      sorter: true,
      width: 100,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索数量单位"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => record['数量单位']?.toString().toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '数量',
      dataIndex: '数量',
      key: '数量',
      sorter: true,
      width: 100,
      render: (text) => text?.toFixed(2),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="最小值"
            value={selectedKeys[0]?.split('-')[0] || ''}
            onChange={e => {
              const max = selectedKeys[0]?.split('-')[1] || '';
              setSelectedKeys(e.target.value || max ? [`${e.target.value}-${max}`] : []);
            }}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Input
            placeholder="最大值"
            value={selectedKeys[0]?.split('-')[1] || ''}
            onChange={e => {
              const min = selectedKeys[0]?.split('-')[0] || '';
              setSelectedKeys(min || e.target.value ? [`${min}-${e.target.value}`] : []);
            }}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => {
        const [min, max] = value.split('-');
        const recordValue = parseFloat(record['数量']);
        if (min && max) return recordValue >= parseFloat(min) && recordValue <= parseFloat(max);
        if (min) return recordValue >= parseFloat(min);
        if (max) return recordValue <= parseFloat(max);
        return true;
      },
    },
    {
      title: '公吨',
      dataIndex: '公吨',
      key: '公吨',
      sorter: true,
      width: 100,
      render: (text) => text?.toFixed(4),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="最小值"
            value={selectedKeys[0]?.split('-')[0] || ''}
            onChange={e => {
              const max = selectedKeys[0]?.split('-')[1] || '';
              setSelectedKeys(e.target.value || max ? [`${e.target.value}-${max}`] : []);
            }}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Input
            placeholder="最大值"
            value={selectedKeys[0]?.split('-')[1] || ''}
            onChange={e => {
              const min = selectedKeys[0]?.split('-')[0] || '';
              setSelectedKeys(min || e.target.value ? [`${min}-${e.target.value}`] : []);
            }}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => {
        const [min, max] = value.split('-');
        const recordValue = parseFloat(record['公吨']);
        if (min && max) return recordValue >= parseFloat(min) && recordValue <= parseFloat(max);
        if (min) return recordValue >= parseFloat(min);
        if (max) return recordValue <= parseFloat(max);
        return true;
      },
    },
    {
      title: '金额美元',
      dataIndex: '金额美元',
      key: '金额美元',
      sorter: true,
      width: 120,
      render: (text) => text?.toFixed(2),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="最小值"
            value={selectedKeys[0]?.split('-')[0] || ''}
            onChange={e => {
              const max = selectedKeys[0]?.split('-')[1] || '';
              setSelectedKeys(e.target.value || max ? [`${e.target.value}-${max}`] : []);
            }}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Input
            placeholder="最大值"
            value={selectedKeys[0]?.split('-')[1] || ''}
            onChange={e => {
              const min = selectedKeys[0]?.split('-')[0] || '';
              setSelectedKeys(min || e.target.value ? [`${min}-${e.target.value}`] : []);
            }}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => {
        const [min, max] = value.split('-');
        const recordValue = parseFloat(record['金额美元']);
        if (min && max) return recordValue >= parseFloat(min) && recordValue <= parseFloat(max);
        if (min) return recordValue >= parseFloat(min);
        if (max) return recordValue <= parseFloat(max);
        return true;
      },
    },
    {
      title: '详细产品名称',
      dataIndex: '详细产品名称',
      key: '详细产品名称',
      sorter: true,
      width: 200,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索产品名称"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => record['详细产品名称']?.toString().toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '提单号',
      dataIndex: '提单号',
      key: '提单号',
      sorter: true,
      width: 150,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索提单号"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => record['提单号']?.toString().toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '数据来源',
      dataIndex: '数据来源',
      key: '数据来源',
      sorter: true,
      width: 120,
      filters: [
        { text: '海关总署', value: '海关总署' },
        { text: '进出口数据', value: '进出口数据' },
        { text: '贸易统计', value: '贸易统计' },
        { text: '第三方数据', value: '第三方数据' },
      ],
      onFilter: (value, record) => record['数据来源'] === value,
    },
    {
      title: '关单号',
      dataIndex: '关单号',
      key: '关单号',
      sorter: true,
      width: 150,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索关单号"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) => record['关单号']?.toString().toLowerCase().includes(value.toLowerCase()),
    },
    // 操作列，根据权限显示
    ...(hasPermission(PERMISSIONS.DATA_UPDATE) || hasPermission(PERMISSIONS.DATA_DELETE) ? [{
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          {hasPermission(PERMISSIONS.DATA_UPDATE) && (
            <Button type="primary" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
              编辑
            </Button>
          )}
          {hasPermission(PERMISSIONS.DATA_DELETE) && (
            <Button danger size="small" icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>
              删除
            </Button>
          )}
        </Space>
      ),
      width: 180,
      fixed: 'right',
    }] : [])
  ];

  return (
    <div className="data-query-page" style={{height: '100%', display: 'flex', flexDirection: 'column',margin: '0 20px'}}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <Title level={2}>海关数据查询</Title>
        <Space size="middle">
          {/* 导出按钮 - 需要数据导出权限 */}
          {hasPermission(PERMISSIONS.DATA_EXPORT) && (
            <Button icon={<DownloadOutlined />} disabled={dataSource.length === 0} size="middle" onClick={handleExport}>
              导出
            </Button>
          )}
          {/* 新增数据按钮 - 需要数据创建权限 */}
          {hasPermission(PERMISSIONS.DATA_CREATE) && (
            <Button type="primary" onClick={() => { setCurrentRecord(null); editForm.resetFields(); editForm.setFieldsValue({日期: null,});setEditModalVisible(true); }}>
              新增数据
            </Button>
          )}
          {/* 批量删除按钮 - 需要数据删除权限 */}
          {hasPermission(PERMISSIONS.DATA_DELETE) && (
            <Button danger icon={<DeleteOutlined />} size="middle" onClick={handleBulkDelete} disabled={dataSource.length === 0}>
              批量删除当前结果
            </Button>
          )}
        </Space>
      </div>
      
      <div style={{ display:"flex", height:"0" ,flex:1}} >
        <div style={{height: "100%",flex:1,marginRight:16 }} >
          <div style={{background:"#fff",height:"100%",width:"100%",borderRadius:8,padding:16}}>
            <Form
              style={{height:"100%", overflowY:"auto", overflowX:"hidden"}}
              form={form}
              layout="vertical"
              onFinish={handleSearch}
              initialValues={{ sort_by: '日期', sort_order: 'desc' }}
              className="query-form"
            >
              <Row gutter={[16, 0]}>
                <Col xs={24} sm={24} md={24} lg={24} xl={24}>
                  <Form.Item name="customs_code" label="海关编码">
                    <Select
                      showSearch
                      allowClear
                      placeholder="选择或输入海关编码"
                      style={{ width: '100%' }}
                      filterOption={(input, option) =>
                        (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                      }
                    >
                      {(customsCodes || []).map(code => (
                        <Option key={code} value={code}>{code}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>

                <Col xs={24} sm={24} md={24} lg={24} xl={24}>
                  <Form.Item name="import_country" label="进口国家">
                    <Select
                      showSearch
                      allowClear
                      placeholder="选择进口国家"
                      style={{ width: '100%' }}
                      filterOption={(input, option) =>
                        (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                      }
                    >
                      {(countries.import || []).map(country => (
                        <Option key={country} value={country}>{country}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>

                <Col xs={24} sm={24} md={24} lg={24} xl={24}>
                  <Form.Item name="export_country" label="出口国家">
                    <Select
                      showSearch
                      allowClear
                      placeholder="选择出口国家"
                      style={{ width: '100%' }}
                      filterOption={(input, option) =>
                        (option?.children ?? '').toLowerCase().includes(input.toLowerCase())
                      }
                    >
                      {(countries.export || []).map(country => (
                        <Option key={country} value={country}>{country}</Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>

                <Col xs={24} sm={24} md={24} lg={24} xl={24}>
                  <Form.Item name="date_range" label="日期范围">
                    <RangePicker
                      format="YYYY-MM-DD"
                      style={{ width: '100%' }}
                      placeholder={['开始日期', '结束日期']}
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} sm={24} md={24} lg={24} xl={24}>
                  <Form.Item name="importer" label="进口商">
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <AutoComplete
                        style={{ flex: 1 }}
                        placeholder="输入进口商名称"
                        onSearch={handleImporterSearch}
                        options={(suggestions.importers || []).map(item => ({ value: item }))}
                        filterOption={false}
                        allowClear
                      />
                      <Button 
                        type={fuzzySearch.importer ? "primary" : "default"}
                        onClick={() => setFuzzySearch(prev => ({ ...prev, importer: !prev.importer }))}
                        size="middle"
                      >
                        模糊
                      </Button>
                    </div>
                  </Form.Item>
                </Col>

               <Col xs={24} sm={24} md={24} lg={24} xl={24}>
                  <Form.Item name="exporter" label="出口商">
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <AutoComplete
                        style={{ flex: 1 }}
                        placeholder="输入出口商名称"
                        onSearch={handleExporterSearch}
                        options={(suggestions.exporters || []).map(item => ({ value: item }))}
                        filterOption={false}
                        allowClear
                      />
                      <Button 
                        type={fuzzySearch.exporter ? "primary" : "default"}
                        onClick={() => setFuzzySearch(prev => ({ ...prev, exporter: !prev.exporter }))}
                        size="middle"
                      >
                        模糊
                      </Button>
                    </div>
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
                  </Space>
                </Col>
              </Row>
            </Form>
          </div>
        </div>
        <div  style={{height:"100%",flex:3,width:0}}>
          <div className="table-1" style={{background:"#fff",height:"100%",width:"100%",borderRadius:8,padding:16}}>
            <Spin style={{height:"100%"}} spinning={loading} tip="数据加载中...">
              <div className="ad-body-table" style={{height:"100%"}}>
                <Table
                  columns={columns}
                  dataSource={dataSource.map((item, index) => ({ ...item, key: index }))}
                  pagination={pagination}
                  onChange={handleTableChange}
                  size="middle"
                  bordered
                  scroll={{ x: 'max-content', y: 'calc(100% - 40px)' }}
                  style={{height:"100%"}}
                />
              </div> 
            </Spin>
          </div>
        </div>
      </div>

      {/* 编辑/新增数据模态框 - 根据权限显示 */}
      {(hasPermission(PERMISSIONS.DATA_CREATE) || hasPermission(PERMISSIONS.DATA_UPDATE)) && (
        <Modal
          title={currentRecord ? "编辑数据" : "新增数据"}
          open={editModalVisible}
          onCancel={() => setEditModalVisible(false)}
          footer={[
            <Button key="cancel" onClick={() => setEditModalVisible(false)}>取消</Button>,
            <Button key="save" type="primary" loading={loading} onClick={handleSaveEdit}>保存</Button>
          ]}
          destroyOnClose
          width={800}
        >
        <Form form={editForm} layout="vertical" initialValues={currentRecord || {}}>
          <Form.Item name="海关编码" label="海关编码" rules={[{ required: true, message: '请输入海关编码' }]}>
            <Input placeholder="请输入海关编码" />
          </Form.Item>
          <Form.Item name="编码产品描述" label="编码产品描述" rules={[{message: '请输入编码产品描述' }]}>
            <Input placeholder="请输入编码产品描述" />
          </Form.Item>
          <Form.Item name="日期" label="日期" rules={[{ required: true, message: '请选择日期' }]}>
            <DatePicker format="YYYY-MM-DD" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="进口商" label="进口商" rules={[{ required: true, message: '请输入进口商' }]}>
            <Input placeholder="请输入进口商" />
          </Form.Item>
          <Form.Item name="进口商所在国家" label="进口国家" rules={[{ required: true, message: '请选择进口国家' }]}>
            <Select placeholder="请选择进口国家">
              {(countries.import || []).map(country => (
                <Option key={country} value={country}>{country}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="出口商" label="出口商" rules={[{ required: true, message: '请输入出口商' }]}>
            <Input placeholder="请输入出口商" />
          </Form.Item>
          <Form.Item name="出口商所在国家" label="出口国家" rules={[{ required: true, message: '请选择出口国家' }]}>
            <Select placeholder="请选择出口国家">
              {(countries.export || []).map(country => (
                <Option key={country} value={country}>{country}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="数量单位" label="数量单位" rules={[{ required: true, message: '请输入数量单位' }]}>
            <Input placeholder="请输入数量单位" />
          </Form.Item>
          <Form.Item name="数量" label="数量" rules={[{ required: true, message: '请输入数量' }]}>
            <Input type="number" placeholder="请输入数量" />
          </Form.Item>
          <Form.Item name="公吨" label="公吨">
            <Input type="number" placeholder="请输入公吨" />
          </Form.Item>
          <Form.Item name="金额美元" label="金额美元" rules={[{ required: true, message: '请输入金额美元' }]}>
            <Input type="number" placeholder="请输入金额美元" />
          </Form.Item>
          <Form.Item name="详细产品名称" label="详细产品名称" rules={[{message: '请输入详细产品名称' }]}>
            <Input placeholder="请输入详细产品名称" />
          </Form.Item>
          <Form.Item name="提单号" label="提单号" rules={[{message: '请输入提单号' }]}>
            <Input placeholder="请输入提单号" />
          </Form.Item>
          <Form.Item name="数据来源" label="数据来源" rules={[{ message: '请输入数据来源' }]}>
            <Input placeholder="请输入数据来源" />
          </Form.Item>
          <Form.Item name="关单号" label="关单号" rules={[{ message: '请输入关单号' }]}>
            <Input placeholder="请输入关单号" />
          </Form.Item>
        </Form>
      </Modal>
    )}

      {/* 批量删除确认对话框 - 根据权限显示 */}
      {hasPermission(PERMISSIONS.DATA_DELETE) && (
        <Modal
          title="确认删除"
          open={showDeleteConfirm}
          onCancel={() => setShowDeleteConfirm(false)}
          footer={[
            <Button key="cancel" onClick={() => setShowDeleteConfirm(false)}>取消</Button>,
            <Button key="current" type="primary" danger loading={loading} onClick={() => confirmDelete(false)}>
              删除当前显示的 {dataSource.length} 条记录
            </Button>,
            <Button key="all" type="primary" danger loading={loading} onClick={() => confirmDelete(true)}>
              删除所有符合条件的记录
            </Button>
          ]}
        >
          <p>请选择删除范围：</p>
          <p>• <strong>删除当前显示的记录</strong>：仅删除当前页面显示的 {dataSource.length} 条记录</p>
          <p>• <strong>删除所有符合条件的记录</strong>：删除所有符合当前搜索条件的记录（可能包含多页数据）</p>
          <p style={{color: 'red', fontWeight: 'bold'}}>⚠️ 此操作不可撤销，请谨慎选择！</p>
        </Modal>
      )}
    </div>
  );
};

export default DataQuery;