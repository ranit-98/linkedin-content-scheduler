export type TPostStatus = 'scheduled' | 'processing' | 'published' | 'failed';
export type TSchedulePostParamType = {
  connection_id: string;
  content: string;
  scheduled_at: string;
  max_attempts: number;
  image_base64?: string;
  image_content_type?: string;
  image_filename?: string;
};
