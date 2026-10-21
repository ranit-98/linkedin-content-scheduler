'use client';

import ArrowForwardRoundedIcon from '@mui/icons-material/ArrowForwardRounded';
import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import LockRoundedIcon from '@mui/icons-material/LockRounded';
import ScienceRoundedIcon from '@mui/icons-material/ScienceRounded';
import { Box, Button, CircularProgress, Typography } from '@mui/material';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { getLinkedInAuthorizeUrl } from '@/api/endpoints';
import {
  useCreateMockLinkedInConnection,
  useLinkedInConnections,
} from '@/api/hooks/linkedin/hooks';
import { hasActiveSession, startSession } from '../session';

const benefits = [
  'Schedule posts for an exact date and time',
  'Automatic retry for temporary LinkedIn errors',
  'Track scheduled, processing, published, and failed posts',
];

export default function LoginPage() {
  //================================>
  // Existing connection check and local-demo mutation
  //================================>
  const router = useRouter();
  const connections = useLinkedInConnections();
  const mockConnection = useCreateMockLinkedInConnection(() => {
    startSession();
    router.replace('/');
  });

  useEffect(() => {
    if (connections.isSuccess && connections.data.length > 0 && hasActiveSession()) {
      router.replace('/');
    }
  }, [connections.data, connections.isSuccess, router]);

  //================================>
  // OAuth handler – LinkedIn collects credentials and the backend completes the exchange
  //================================>
  const handleLinkedInLogin = () => {
    window.location.assign(getLinkedInAuthorizeUrl());
  };

  if (connections.isLoading) {
    return (
      <Box className="login-loading">
        <CircularProgress size={30} />
      </Box>
    );
  }

  return (
    <Box className="login-shell">
      <Box className="login-story">
        <Box className="login-brand">
          <Box>
            <LinkedInIcon />
          </Box>
          <Typography component="span">PostPilot</Typography>
        </Box>

        <Box className="login-message">
          <Typography variant="overline">LinkedIn publishing, simplified</Typography>
          <Typography variant="h2">Write today. Show up at the right moment.</Typography>
          <Typography className="login-description">
            A dependable publishing workspace for scheduling one thoughtful LinkedIn post and
            following it all the way to delivery.
          </Typography>
          <Box className="benefit-list">
            {benefits.map((benefit) => (
              <Box key={benefit}>
                <CheckCircleRoundedIcon />
                <Typography>{benefit}</Typography>
              </Box>
            ))}
          </Box>
        </Box>

        <Typography className="login-footnote" variant="caption">
          Built with durable scheduling and duplicate-post protection.
        </Typography>
      </Box>

      <Box component="main" className="login-panel">
        <Box className="login-card">
          <Box className="linkedin-login-icon">
            <LinkedInIcon />
          </Box>
          <Typography variant="h4">Connect your LinkedIn</Typography>
          <Typography color="text.secondary">
            Sign in with LinkedIn to give PostPilot permission to publish the post you schedule.
          </Typography>

          <Button
            fullWidth
            size="large"
            variant="contained"
            startIcon={<LinkedInIcon />}
            endIcon={<ArrowForwardRoundedIcon />}
            onClick={handleLinkedInLogin}
          >
            Continue with LinkedIn
          </Button>

          <Box className="oauth-security-note">
            <LockRoundedIcon />
            <Typography variant="caption">
              Your password is entered on LinkedIn. This app never sees or stores it. Access tokens
              are encrypted by the backend.
            </Typography>
          </Box>

          <Box className="login-divider">
            <span />
            <Typography variant="caption">LOCAL DEVELOPMENT</Typography>
            <span />
          </Box>

          <Button
            fullWidth
            variant="outlined"
            startIcon={<ScienceRoundedIcon />}
            disabled={mockConnection.isPending}
            onClick={() => mockConnection.mutate()}
          >
            {mockConnection.isPending ? 'Creating demo connection…' : 'Use demo connection'}
          </Button>
          <Typography variant="caption" color="text.secondary" textAlign="center">
            Demo access works when the backend has LINKEDIN_MOCK_MODE=true.
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
