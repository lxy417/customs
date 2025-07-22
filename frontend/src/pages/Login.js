import React, { useEffect } from 'react';
import { Form, Input, Button, Card, Space, Typography, Layout } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Login.css';

const { Title } = Typography;
const { Header, Content } = Layout;

const Login = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loading, isAuthenticated } = useAuth();

  // 获取登录前的位置，默认为首页
  const from = location.state?.from?.pathname || '/home';

  // 检查用户是否已登录，如果已登录则跳转到首页
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/home', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (values) => {
    const success = await login(values.username, values.password);
    if (success) {
      navigate(from, { replace: true });
    }
  };

  return (
    
    <Layout className="login-layout">
      
      <Header className="login-header">
        <Title level={3}>精算平台</Title>
      </Header>
      <Content className="login-content">
        <Card className="login-card" title={<Title level={4}>用户登录</Title>}>
          <Form
            form={form}
            name="login_form"
            layout="vertical"
            onFinish={handleSubmit}
            initialValues={{ remember: true }}
          >
            <Form.Item
              name="username"
              label="用户名"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input prefix={<UserOutlined />} placeholder="请输入用户名" />
            </Form.Item>

            <Form.Item
              name="password"
              label="密码"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="请输入密码" />
            </Form.Item>

            <Form.Item>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  登录
                </Button>
                <div style={{ textAlign: 'center', fontSize: '12px', color: '#999' }}>
                  默认管理员账号: admin / admin123
                </div>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      </Content>
    </Layout>
  );
};

export default Login;