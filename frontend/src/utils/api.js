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
    // 从本地存储获取token并添加到请求头
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
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
  search: (params) => api.get('/api/v1/data/search', { params }),
  export: (params) => api.get('/api/v1/data/search', { params }),
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

export const userAPI = {
  createUser: (userData) => api.post('/api/v1/user', userData),
  updateUser: (username, userData) => api.put(`/api/v1/user/${username}`, userData),
  deleteUser: (username) => api.delete(`/api/v1/user/${username}`),
  getUsers: () => api.get('/api/v1/user'),
  getUser: (username) => api.get(`/api/v1/user/${username}`)
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

export default api;