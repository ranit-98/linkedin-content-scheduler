'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  createMockLinkedInConnectionFn,
  createScheduledPostFn,
  getLinkedInConnectionsFn,
  getScheduledPostsFn,
} from '@/api/functions/linkedin/index.api';
import { LinkedInQueryKey } from './key';

export const useLinkedInConnections = () =>
  useQuery({
    queryKey: [LinkedInQueryKey.Connections],
    queryFn: getLinkedInConnectionsFn,
    select: (res) => res.data,
  });
export const useScheduledPosts = () =>
  useQuery({
    queryKey: [LinkedInQueryKey.Posts],
    queryFn: getScheduledPostsFn,
    select: (res) => res.data,
    refetchInterval: 5000,
  });
export const useCreateMockLinkedInConnection = (optionalCallback: () => void = () => {}) => {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [LinkedInQueryKey.CreateMock],
    mutationFn: createMockLinkedInConnectionFn,
    onSuccess: async () => {
      toast.success('Demo account connected');
      await client.invalidateQueries({ queryKey: [LinkedInQueryKey.Connections] });
      optionalCallback();
    },
  });
};
export const useCreateScheduledPost = (callback: () => void) => {
  const client = useQueryClient();
  return useMutation({
    mutationKey: [LinkedInQueryKey.CreatePost],
    mutationFn: createScheduledPostFn,
    onSuccess: async (_response, variables) => {
      const isPublishingNow = new Date(variables.scheduled_at).getTime() <= Date.now();
      toast.success(isPublishingNow ? 'Post queued for publishing' : 'Post scheduled successfully');
      callback();
      await client.invalidateQueries({ queryKey: [LinkedInQueryKey.Posts] });
    },
  });
};
