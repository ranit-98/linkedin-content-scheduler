import type { TPostStatus } from '@/types/apps/linkedin/index.type';
export interface ILinkedInConnectionResponse {
  id: string;
  linkedin_member_id: string;
  display_name: string | null;
  token_expires_at: string;
  scopes: string;
  created_at: string;
}
export interface IScheduledPostResponse {
  id: string;
  connection_id: string;
  content: string;
  has_image: boolean;
  image_filename: string | null;
  scheduled_at: string;
  next_attempt_at: string;
  status: TPostStatus;
  attempt_count: number;
  max_attempts: number;
  idempotency_key: string;
  linkedin_post_urn: string | null;
  last_error: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}
