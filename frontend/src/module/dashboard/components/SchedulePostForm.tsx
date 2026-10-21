'use client';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import EventRoundedIcon from '@mui/icons-material/EventRounded';
import ImageRoundedIcon from '@mui/icons-material/ImageRounded';
import RocketLaunchRoundedIcon from '@mui/icons-material/RocketLaunchRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import UploadRoundedIcon from '@mui/icons-material/UploadRounded';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Button,
  ButtonGroup,
  FormLabel,
  IconButton,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import { type ChangeEvent, useEffect, useRef, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import toast from 'react-hot-toast';
import { FormInputField, FormSelect } from '@/@core/components/form-inputs';
import { useCreateScheduledPost } from '@/api/hooks/linkedin/hooks';
import type { ILinkedInConnectionResponse } from '@/types/interface/linkedin/index.interface';
import { schedulePostSchema, type TSchedulePostSchemaType } from '../validation/schedulePost.zod';

const localDateTime = (date: Date) => {
  const d = new Date(date);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
};

const defaultScheduleTime = () => localDateTime(new Date(Date.now() + 5 * 60 * 1000));

const allowedImageTypes = new Set(['image/jpeg', 'image/png', 'image/gif']);
const maxImageBytes = 5 * 1024 * 1024;

const readBase64 = (file: File) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '');
    reader.onerror = () => reject(new Error('Could not read the selected image'));
    reader.readAsDataURL(file);
  });

export default function SchedulePostForm({
  connection,
}: {
  connection: ILinkedInConnectionResponse | null;
}) {
  //================================>
  // Validated scheduling form and live character count
  //================================>
  const form = useForm<TSchedulePostSchemaType>({
    resolver: zodResolver(schedulePostSchema()),
    defaultValues: {
      content: '',
      publishMode: 'now',
      scheduledAt: defaultScheduleTime(),
      maxAttempts: 5,
    },
  });
  const content = useWatch({ control: form.control, name: 'content' }) ?? '';
  const publishMode = useWatch({ control: form.control, name: 'publishMode' }) ?? 'now';
  const imageInput = useRef<HTMLInputElement>(null);
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (imagePreview) URL.revokeObjectURL(imagePreview);
    };
  }, [imagePreview]);

  const clearImage = () => {
    setImage(null);
    setImagePreview(null);
    if (imageInput.current) imageInput.current.value = '';
  };

  const chooseImage = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (!selected) return;
    if (!allowedImageTypes.has(selected.type)) {
      toast.error('Choose a JPEG, PNG, or GIF image');
      event.target.value = '';
      return;
    }
    if (selected.size > maxImageBytes) {
      toast.error('Image must be 5 MB or smaller');
      event.target.value = '';
      return;
    }
    setImage(selected);
    setImagePreview(URL.createObjectURL(selected));
  };
  //================================>
  // Publish mutation and form reset after success
  //================================>
  const create = useCreateScheduledPost(() => {
    form.reset({
      content: '',
      publishMode: 'now',
      scheduledAt: defaultScheduleTime(),
      maxAttempts: 5,
    });
    clearImage();
  });
  const submit = async (data: TSchedulePostSchemaType) => {
    if (!connection) return;
    const imageBase64 = image ? await readBase64(image) : undefined;
    create.mutate({
      connection_id: connection.id,
      content: data.content.trim(),
      scheduled_at:
        data.publishMode === 'now'
          ? new Date().toISOString()
          : new Date(data.scheduledAt).toISOString(),
      max_attempts: data.maxAttempts,
      ...(image && imageBase64
        ? {
            image_base64: imageBase64,
            image_content_type: image.type,
            image_filename: image.name,
          }
        : {}),
    });
  };
  return (
    <Box className="card">
      <Box className="card-head">
        <Box>
          <Typography variant="overline">Create</Typography>
          <Typography variant="h5">Create a post</Typography>
        </Box>
        <Typography className="focus-pill">✦ Focused writing</Typography>
      </Box>
      <Box component="form" onSubmit={form.handleSubmit(submit)}>
        <Stack spacing={2.5}>
          <Box>
            <FormInputField
              control={form.control}
              name="content"
              label="Post content"
              placeholder="Share an idea, lesson, or update with your network…"
              multiline
              minRows={7}
              slotProps={{ htmlInput: { maxLength: 3000 } }}
            />
            <Box className="count">
              <LinearProgress variant="determinate" value={content.length / 30} />
              <Typography variant="caption">{content.length} / 3,000</Typography>
            </Box>
          </Box>
          <Box className="image-upload">
            <Box className="upload-label">
              <Typography component="label" fontWeight={750} fontSize={13}>
                Image <span>Optional</span>
              </Typography>
              <Typography variant="caption">JPEG, PNG or GIF · up to 5 MB</Typography>
            </Box>
            <input
              ref={imageInput}
              hidden
              type="file"
              accept="image/jpeg,image/png,image/gif"
              onChange={chooseImage}
            />
            {imagePreview && image ? (
              <Box className="image-preview">
                <Box component="img" src={imagePreview} alt="Selected post image preview" />
                <Box className="image-meta">
                  <ImageRoundedIcon />
                  <Box className="grow">
                    <Typography fontWeight={750} noWrap>
                      {image.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {(image.size / 1024 / 1024).toFixed(1)} MB
                    </Typography>
                  </Box>
                  <IconButton aria-label="Remove selected image" onClick={clearImage}>
                    <CloseRoundedIcon />
                  </IconButton>
                </Box>
              </Box>
            ) : (
              <Button
                className="upload-button"
                variant="outlined"
                startIcon={<UploadRoundedIcon />}
                onClick={() => imageInput.current?.click()}
              >
                Upload an image
              </Button>
            )}
          </Box>
          <Box className="publish-mode">
            <FormLabel>When should this be published?</FormLabel>
            <ButtonGroup fullWidth aria-label="Choose when to publish">
              <Button
                variant={publishMode === 'now' ? 'contained' : 'outlined'}
                startIcon={<RocketLaunchRoundedIcon />}
                aria-pressed={publishMode === 'now'}
                onClick={() => form.setValue('publishMode', 'now', { shouldValidate: true })}
              >
                Post now
              </Button>
              <Button
                variant={publishMode === 'scheduled' ? 'contained' : 'outlined'}
                startIcon={<EventRoundedIcon />}
                aria-pressed={publishMode === 'scheduled'}
                onClick={() => form.setValue('publishMode', 'scheduled', { shouldValidate: true })}
              >
                Schedule post
              </Button>
            </ButtonGroup>
          </Box>
          <Box className={`form-grid ${publishMode === 'now' ? 'retry-only' : ''}`}>
            {publishMode === 'scheduled' && (
              <FormInputField
                control={form.control}
                name="scheduledAt"
                label="Publish date & time"
                type="datetime-local"
                slotProps={{ htmlInput: { min: localDateTime(new Date()) } }}
              />
            )}
            <FormSelect
              control={form.control}
              name="maxAttempts"
              label="Retry attempts"
              options={[1, 3, 5, 7, 10].map((v) => ({ label: String(v), value: v }))}
            />
          </Box>
          <Button
            type="submit"
            variant="contained"
            size="large"
            endIcon={<SendRoundedIcon />}
            disabled={create.isPending || !connection}
          >
            {create.isPending
              ? publishMode === 'now'
                ? 'Posting…'
                : 'Scheduling…'
              : publishMode === 'now'
                ? 'Post now'
                : 'Schedule post'}
          </Button>
        </Stack>
      </Box>
    </Box>
  );
}
