'use client';
import AccessTimeRoundedIcon from '@mui/icons-material/AccessTimeRounded';
import ChatBubbleOutlineRoundedIcon from '@mui/icons-material/ChatBubbleOutlineRounded';
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import ImageRoundedIcon from '@mui/icons-material/ImageRounded';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import MoreHorizRoundedIcon from '@mui/icons-material/MoreHorizRounded';
import PublicRoundedIcon from '@mui/icons-material/PublicRounded';
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded';
import RepeatRoundedIcon from '@mui/icons-material/RepeatRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import ThumbUpAltOutlinedIcon from '@mui/icons-material/ThumbUpAltOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { getPostImageUrl } from '@/api/endpoints';
import type { IScheduledPostResponse } from '@/types/interface/linkedin/index.interface';

const colors = {
  scheduled: 'warning',
  processing: 'info',
  published: 'success',
  failed: 'error',
} as const;

const postDate = (post: IScheduledPostResponse) => new Date(post.published_at ?? post.scheduled_at);

export default function PostActivity({
  posts,
  authorName,
  loading,
  fetching,
  refresh,
}: {
  posts: IScheduledPostResponse[];
  authorName: string;
  loading: boolean;
  fetching: boolean;
  refresh: () => void;
}) {
  const [selectedPost, setSelectedPost] = useState<IScheduledPostResponse | null>(null);
  const authorInitial = authorName.trim().charAt(0).toUpperCase() || 'L';

  return (
    <>
      <Box className="card activity">
        <Box className="card-head ruled">
          <Box>
            <Typography variant="overline">Timeline</Typography>
            <Typography variant="h5">Publishing activity</Typography>
          </Box>
          <Button
            size="small"
            startIcon={fetching ? <CircularProgress size={15} /> : <RefreshRoundedIcon />}
            onClick={refresh}
          >
            Refresh
          </Button>
        </Box>
        {loading ? (
          <Box className="center">
            <CircularProgress />
          </Box>
        ) : !posts.length ? (
          <Box className="empty activity-empty">
            <Box className="clock">
              <AccessTimeRoundedIcon />
            </Box>
            <Typography fontWeight={800}>Your publishing timeline is clear</Typography>
            <Typography variant="body2" color="text.secondary">
              Scheduled posts and delivery results will appear here.
            </Typography>
          </Box>
        ) : (
          <Box className="activity-list">
            {posts.map((post) => (
              <Box
                component="button"
                type="button"
                className="post"
                key={post.id}
                onClick={() => setSelectedPost(post)}
                aria-label={`Open ${post.status} post preview`}
              >
                <Box className="post-date">
                  <Typography className="post-day">
                    {postDate(post).toLocaleDateString([], { day: '2-digit' })}
                  </Typography>
                  <Typography variant="caption">
                    {postDate(post).toLocaleDateString([], { month: 'short' })}
                  </Typography>
                  <Typography variant="caption">
                    {postDate(post).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </Typography>
                </Box>
                <Box className="grow post-summary">
                  <Typography className="post-copy">{post.content}</Typography>
                  <Box className="post-meta">
                    {post.has_image && (
                      <Typography className="post-media" variant="caption">
                        <ImageRoundedIcon /> Image
                      </Typography>
                    )}
                    <Typography variant="caption" color="text.secondary">
                      {post.attempt_count > 0
                        ? `${post.attempt_count} publish attempt${post.attempt_count === 1 ? '' : 's'}`
                        : 'Ready to publish'}
                    </Typography>
                  </Box>
                </Box>
                <Box className="post-action">
                  <Chip label={post.status} color={colors[post.status]} size="small" />
                  <ChevronRightRoundedIcon />
                </Box>
              </Box>
            ))}
          </Box>
        )}
      </Box>

      <Dialog
        open={Boolean(selectedPost)}
        onClose={() => setSelectedPost(null)}
        fullWidth
        maxWidth="md"
        className="post-preview-dialog"
      >
        <DialogTitle className="preview-title">
          <Box className="preview-network-brand">
            <LinkedInIcon />
            <Box>
              <Typography fontWeight={800}>LinkedIn post preview</Typography>
              <Typography variant="caption">See how your post will appear in the feed</Typography>
            </Box>
          </Box>
          <IconButton aria-label="Close post preview" onClick={() => setSelectedPost(null)}>
            <CloseRoundedIcon />
          </IconButton>
        </DialogTitle>
        {selectedPost && (
          <DialogContent className="preview-content">
            <Box className="linkedin-preview">
              <Box className="linkedin-author">
                <Box className="preview-avatar">{authorInitial}</Box>
                <Box className="grow">
                  <Typography className="preview-author-name">{authorName}</Typography>
                  <Typography className="preview-author-description" variant="caption">
                    LinkedIn member · You
                  </Typography>
                  <Typography className="preview-post-time" variant="caption">
                    {selectedPost.status === 'published'
                      ? postDate(selectedPost).toLocaleDateString([], {
                          month: 'short',
                          day: 'numeric',
                        })
                      : 'Scheduled'}{' '}
                    · <PublicRoundedIcon />
                  </Typography>
                </Box>
                <Box className="preview-more" aria-hidden="true">
                  <MoreHorizRoundedIcon />
                </Box>
              </Box>
              <Typography className="preview-copy">{selectedPost.content}</Typography>
              {selectedPost.has_image && (
                <Box className="preview-image-frame">
                  <Box
                    component="img"
                    className="preview-image"
                    src={getPostImageUrl(selectedPost.id)}
                    alt={selectedPost.image_filename ?? 'LinkedIn post attachment'}
                  />
                </Box>
              )}
              <Box className="preview-engagement">
                <Box className="reaction-stack" aria-hidden="true">
                  <span>👍</span>
                  <span>💡</span>
                  <span>👏</span>
                </Box>
                <Typography variant="caption">Reactions will appear after publishing</Typography>
              </Box>
              <Divider />
              <Box
                className="preview-actions"
                role="group"
                aria-label="LinkedIn post actions preview"
              >
                <Box>
                  <ThumbUpAltOutlinedIcon />
                  <Typography variant="caption">Like</Typography>
                </Box>
                <Box>
                  <ChatBubbleOutlineRoundedIcon />
                  <Typography variant="caption">Comment</Typography>
                </Box>
                <Box>
                  <RepeatRoundedIcon />
                  <Typography variant="caption">Repost</Typography>
                </Box>
                <Box>
                  <SendRoundedIcon />
                  <Typography variant="caption">Send</Typography>
                </Box>
              </Box>
            </Box>

            {selectedPost.last_error && <Alert severity="error">{selectedPost.last_error}</Alert>}

            <Box className="preview-details-heading">
              <Typography fontWeight={800}>Publishing details</Typography>
              <Typography variant="caption" color="text.secondary">
                Delivery information is only visible to you
              </Typography>
            </Box>
            <Box className="preview-details">
              <Box>
                <Typography variant="caption">Status</Typography>
                <Chip
                  label={selectedPost.status}
                  color={colors[selectedPost.status]}
                  size="small"
                />
              </Box>
              <Box>
                <Typography variant="caption">
                  {selectedPost.status === 'published' ? 'Published at' : 'Scheduled for'}
                </Typography>
                <Typography fontWeight={750}>
                  {postDate(selectedPost).toLocaleString([], {
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption">Attempts</Typography>
                <Typography fontWeight={750}>
                  {selectedPost.attempt_count} of {selectedPost.max_attempts}
                </Typography>
              </Box>
            </Box>
          </DialogContent>
        )}
      </Dialog>
    </>
  );
}
