'use client';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import LogoutRoundedIcon from '@mui/icons-material/LogoutRounded';
import { Box, Typography } from '@mui/material';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useLinkedInConnections, useScheduledPosts } from '@/api/hooks/linkedin/hooks';
import ConnectionCard from '../components/ConnectionCard';
import SchedulePostForm from '../components/SchedulePostForm';
import PostActivity from '../components/PostActivity';
import { endSession, hasActiveSession, startSession } from '@/module/auth/session';

export default function DashboardPage() {
  //================================>
  // Dashboard data and OAuth callback feedback
  //================================>
  const connections = useLinkedInConnections();
  const posts = useScheduledPosts();
  const router = useRouter();
  const [sessionReady, setSessionReady] = useState(false);
  const refetchConnections = connections.refetch;
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    if (searchParams.get('linkedin') === 'connected') {
      startSession();
      toast.success('LinkedIn connected successfully');
      window.history.replaceState({}, '', '/');
      void refetchConnections();
    }
    if (!hasActiveSession()) {
      router.replace('/login');
      return;
    }
    setSessionReady(true);
  }, [refetchConnections, router]);
  const allConnections = connections.data ?? [];

  //================================>
  // Connection guard – new visitors complete LinkedIn OAuth before using the dashboard
  //================================>
  useEffect(() => {
    if (sessionReady && connections.isSuccess && allConnections.length === 0) {
      router.replace('/login');
    }
  }, [allConnections.length, connections.isSuccess, router, sessionReady]);

  const allPosts = posts.data ?? [];
  const upcoming = allPosts.filter((p) => ['scheduled', 'processing'].includes(p.status)).length;
  const published = allPosts.filter((p) => p.status === 'published').length;
  if (!sessionReady) return null;

  const connection = allConnections[0] ?? null;
  const logout = () => {
    endSession();
    router.replace('/login');
  };
  return (
    <Box className="shell">
      <Box component="aside" className="sidebar">
        <Box className="brand">
          <Box>
            <LinkedInIcon />
          </Box>
          <span>PostPilot</span>
        </Box>
        <Box component="nav" className="nav">
          <Box className="active">
            <DashboardRoundedIcon />
            <span>Overview</span>
          </Box>
        </Box>
        <Box className="aside-note">
          <Typography fontWeight={800}>Publish thoughtfully.</Typography>
          <Typography variant="caption">Your credentials stay in the API.</Typography>
        </Box>
        <Box component="button" className="logout" onClick={logout}>
          <LogoutRoundedIcon />
          <span>Log out</span>
        </Box>
      </Box>
      <Box component="main" className="main">
        <Box component="header" className="header">
          <Box>
            <Typography variant="overline">Content workspace</Typography>
            <Typography variant="h3">Good ideas deserve good timing.</Typography>
            <Typography color="text.secondary">
              Plan your LinkedIn presence without losing the human touch.
            </Typography>
          </Box>
          <Box className="summary">
            <Box>
              <Typography variant="caption">Upcoming</Typography>
              <Typography variant="h5">{upcoming}</Typography>
            </Box>
            <i />
            <Box>
              <Typography variant="caption">Published</Typography>
              <Typography variant="h5">{published}</Typography>
            </Box>
          </Box>
        </Box>
        <Box className="grid">
          <Box className="left">
            <ConnectionCard connection={connection} loading={connections.isLoading} />
            <SchedulePostForm connection={connection} />
          </Box>
          <PostActivity
            posts={allPosts}
            authorName={connection?.display_name ?? 'LinkedIn member'}
            loading={posts.isLoading}
            fetching={posts.isFetching}
            refresh={() => {
              void posts.refetch();
            }}
          />
        </Box>
      </Box>
    </Box>
  );
}
