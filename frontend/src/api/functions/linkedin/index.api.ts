import axiosInstance from '@/api/axiosInstance';
import { endpoints } from '@/api/endpoints';
import type { TSchedulePostParamType } from '@/types/apps/linkedin/index.type';
import type {
  ILinkedInConnectionResponse,
  IScheduledPostResponse,
} from '@/types/interface/linkedin/index.interface';

//===========================================================\>
// LinkedIn connection API functions
//===========================================================\>
export const getLinkedInConnectionsFn = () =>
  axiosInstance.get<ILinkedInConnectionResponse[]>(endpoints.connections.list);
export const createMockLinkedInConnectionFn = () =>
  axiosInstance.post<ILinkedInConnectionResponse>(endpoints.connections.mock);

//===========================================================\>
// Scheduled post API functions
//===========================================================\>
export const getScheduledPostsFn = () =>
  axiosInstance.get<IScheduledPostResponse[]>(endpoints.posts.list, { params: { limit: 50 } });
export const createScheduledPostFn = (body: TSchedulePostParamType) =>
  axiosInstance.post<IScheduledPostResponse>(endpoints.posts.create, body, {
    headers: { 'Idempotency-Key': crypto.randomUUID() },
  });
