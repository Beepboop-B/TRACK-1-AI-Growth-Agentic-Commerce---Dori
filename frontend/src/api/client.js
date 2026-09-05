import axios from 'axios';

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: BACKEND_URL,
});

export const getCatalog = async () => {
  const res = await api.get('/catalog');
  return res.data.products || res.data;
};

export const getTransactions = async () => {
  const res = await api.get('/transactions');
  return res.data.transactions || res.data;
};

export const submitIntent = async (query) => {
  const res = await api.post('/agent/buyer/intent', { query });
  return res.data;
};

export const negotiate = async (payload) => {
  const res = await api.post('/agent/negotiate', payload);
  return res.data;
};

export const checkPaymentStatus = async (orderId) => {
  const res = await api.get(`/agent/payment-status/${orderId}`);
  return res.data;
};

export const getAuthStatus = async (token) => {
  const res = await api.get(`/agent/authorization/${token}`);
  return res.data;
};

export const updateAuthStatus = async (token, action, device) => {
  const res = await api.post(`/agent/authorization/${token}`, { action, device });
  return res.data;
};

export const sendApprovalEmail = async (token, email) => {
  const res = await api.post(`/agent/authorization/${token}/email`, { email });
  return res.data;
};
