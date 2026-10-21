import axios, { AxiosError } from 'axios';
import toast from 'react-hot-toast';
import { apiBaseUrl } from '@/api/endpoints';
const axiosInstance = axios.create({ baseURL: apiBaseUrl, timeout: 20000 });
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    toast.error(
      error.response?.data?.detail ??
        (error.code === 'ERR_NETWORK'
          ? 'Unable to reach the API. Make sure the backend is running.'
          : 'Something went wrong.'),
    );
    return Promise.reject(error);
  },
);
export default axiosInstance;
