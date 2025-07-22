import axios from 'axios';
import { message } from 'antd';


// 创建axios实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    debugger
    console.log('=== 发送请求详情 ===');
    console.log('请求URL:', config.baseURL + config.url);
    console.log('请求方法:', config.method);
    console.log('请求头:', config.headers);
    console.log('请求参数:', config.params);
    console.log('请求数据:', config.data);
    console.log('环境变量 REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
    console.log('===================');
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('=== 收到响应详情 ===');
    console.log('响应状态:', response.status);
    console.log('响应头:', response.headers);
    console.log('响应数据:', response.data);
    console.log('===================');
    return response.data;
  },
  (error) => {
    console.error('=== 响应错误详情 ===');
    console.error('错误对象:', error);
    console.error('错误消息:', error.message);
    console.error('错误代码:', error.code);
    console.error('请求配置:', error.config);
    console.error('响应数据:', error.response?.data);
    console.error('响应状态:', error.response?.status);
    console.error('===================');
    const status = error.response?.status;
    let errorMsg = '操作失败，请重试';
    if (error.response?.data) {
      if (Array.isArray(error.response.data.detail)) {
        errorMsg = error.response.data.detail.map(item => item.msg).join('; ');
      } else if (typeof error.response.data.detail === 'string') {
        errorMsg = error.response.data.detail;
      } else {
        errorMsg = JSON.stringify(error.response.data);
      }
    }

    // 处理401未授权错误
    if (status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
      message.error('登录已过期，请重新登录');
    } else if (status === 403) {
      message.error('没有权限执行此操作');
    } else if (status === 500) {
      message.error('服务器内部错误，请稍后再试');
    } else {
      message.error(errorMsg);
    }

    return Promise.reject(error);
  }
);

// 身份验证相关API
export const authAPI = {
  login: (username, password) => {
  const data = new URLSearchParams();
  data.append('username', username);
  data.append('password', password);
  return api.post('/api/v1/auth/login', data, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
},
  getCurrentUser: () => api.get('/api/v1/auth/me'),
  logout: () => api.post('/api/v1/auth/logout')
};

// 数据查询相关API
export const dataAPI = {
  // 数据相关API
  // 搜索海关数据（支持模糊查询）
  searchData: (params) => api.get('/api/v1/data/search', { params }),
  
  // 获取进口商建议
  getImportersSuggestions: (query, limit = 10) => 
    api.get('/api/v1/data/importers/suggestions', { params: { query, limit } })
      .then(response => response.data),
  
  // 获取出口商建议
  getExportersSuggestions: (query, limit = 10) => 
    api.get('/api/v1/data/exporters/suggestions', { params: { query, limit } })
      .then(response => response.data),

  // 保持原有的search方法以兼容现有代码
  search: (params) => api.get('/api/v1/data/search', { params }).then(response => response.data),
  export: (queryParams) => api.post('/api/v1/data/export', { query_params: queryParams }),
  getCustomsCodes: () => api.get('/api/v1/data/customs-codes'),
  getCountries: () => api.get('/api/v1/data/countries'),
  aiSearch: (searchValue, exportCountries, importCountries) => api.post('/api/v1/ai/search', {
    search_value: searchValue,
    export_countries: exportCountries,
    import_countries: importCountries
  }),
  // 数据管理相关API
  create: (data) => api.post('/api/v1/data', data),
  update: (id, data) => api.put(`/api/v1/data/${id}`, data),
  delete: (id) => api.delete(`/api/v1/data/${id}`),
  bulkDelete: (ids) => api.post('/api/v1/data/bulk-delete', { data_ids: ids }),
  bulkDeleteByCondition: (queryParams) => api.post('/api/v1/data/bulk-delete-by-condition', { query_params: queryParams })
};

// // 用户管理相关API
// export const importAPI = {
//   importExcel: async (file) => {
//     const formData = new FormData();
//     formData.append('file', file);
//     return axios.post('/api/v1/import/', formData, {
//       headers: {
//         'Content-Type': 'multipart/form-data'
//       }
//     });
//   }
// };

// 用户管理相关API
export const userAPI = {
  getUsers: () => api.get('/api/v1/user'),
  createUser: (userData) => api.post('/api/v1/user', userData),
  updateUser: (username, userData) => api.put(`/api/v1/user/${username}`, userData),
  deleteUser: (username) => api.delete(`/api/v1/user/${username}`),
  getUserByUsername: (username) => api.get(`/api/v1/user/${username}`),
  getUsersByGroup: (groupId) => api.get(`/api/v1/user/group/${groupId}`)
};

// 角色管理相关API
export const roleAPI = {
  createRole: (roleData) => api.post('/api/v1/role', roleData),
  updateRole: (roleId, roleData) => api.put(`/api/v1/role/${roleId}`, roleData),
  deleteRole: (roleId) => api.delete(`/api/v1/role/${roleId}`),
  getRoles: () => api.get('/api/v1/role'),
  getRole: (roleId) => api.get(`/api/v1/role/${roleId}`),
  getAvailablePermissions: () => api.get('/api/v1/role/permissions/available')
};

// 用户组管理相关API
export const groupAPI = {
  createGroup: (groupData) => api.post('/api/v1/group', groupData),
  updateGroup: (groupId, groupData) => api.put(`/api/v1/group/${groupId}`, groupData),
  deleteGroup: (groupId) => api.delete(`/api/v1/group/${groupId}`),
  getGroups: () => api.get('/api/v1/group'),
  getGroup: (groupId) => api.get(`/api/v1/group/${groupId}`),
  // 移除 getAvailablePermissions，因为用户组不再管理功能权限
  addUserToGroup: (groupId, username) => api.post(`/api/v1/group/${groupId}/users/${username}`),
  removeUserFromGroup: (groupId, username) => api.delete(`/api/v1/group/${groupId}/users/${username}`)
};

// 数据导入相关API
export const importAPI = {
  importExcel: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/v1/import/excel', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};


// 增强导入API
export const enhancedImportAPI = {
  // 批量上传文件
  uploadFiles: (formData) => {
    return api.post('/api/v1/enhanced-import/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  // 获取导入历史
  getImportHistory: (params = {}) => {
    return api.get('/api/v1/enhanced-import/history', { params });
  },

  // 获取任务详情
  getTaskDetail: (taskId) => {
    return api.get(`/api/v1/enhanced-import/task/${taskId}`);
  },

  // 获取统计信息
  getImportStatistics: () => {
    return api.get('/api/v1/enhanced-import/statistics');
  }
};


export default api;