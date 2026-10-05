import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const getCorridors = async () => {
  const res = await api.get('/network/corridors');
  return res.data;
};

export const buildNetwork = async (payload) => {
  const res = await api.post('/network/build', payload);
  return res.data;
};

export const getDemoConditionScores = async () => {
  const res = await api.get('/condition/demo-scores');
  return res.data;
};

export const calculateConditionScores = async (payload) => {
  const res = await api.post('/condition/calculate-scores', payload);
  return res.data;
};

export const runSimulation = async (payload) => {
  const res = await api.post('/simulation/run', payload);
  return res.data;
};

export const getSimulationComparison = async (networkId) => {
  const res = await api.get(`/simulation/comparison/${networkId}`);
  return res.data;
};

export const validateResults = async (payload) => {
  const res = await api.post('/validation/validate', payload);
  return res.data;
};

export const getObservedTimes = async () => {
  const res = await api.get('/validation/observed-times');
  return res.data;
};

export default api;
