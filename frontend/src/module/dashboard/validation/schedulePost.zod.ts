import { z } from 'zod';
export const schedulePostSchema = () =>
  z
    .object({
      content: z
        .string()
        .trim()
        .min(1, 'Post content is required')
        .max(3000, 'Maximum 3,000 characters'),
      publishMode: z.enum(['now', 'scheduled']),
      scheduledAt: z.string(),
      maxAttempts: z.coerce.number().int().min(1).max(10),
    })
    .superRefine(({ publishMode, scheduledAt }, context) => {
      if (publishMode !== 'scheduled') return;
      if (!scheduledAt) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['scheduledAt'],
          message: 'Date and time are required',
        });
      } else if (
        !Number.isFinite(new Date(scheduledAt).getTime()) ||
        new Date(scheduledAt).getTime() <= Date.now()
      ) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['scheduledAt'],
          message: 'Schedule time must be in the future',
        });
      }
    });
export type TSchedulePostSchemaType = z.infer<ReturnType<typeof schedulePostSchema>>;
