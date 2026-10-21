'use client';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import ScienceRoundedIcon from '@mui/icons-material/ScienceRounded';
import { Box, Button, Chip, CircularProgress, Typography } from '@mui/material';
import { getLinkedInAuthorizeUrl } from '@/api/endpoints';
import { useCreateMockLinkedInConnection } from '@/api/hooks/linkedin/hooks';
import type { ILinkedInConnectionResponse } from '@/types/interface/linkedin/index.interface';

export default function ConnectionCard({
  connection,
  loading,
}: {
  connection: ILinkedInConnectionResponse | null;
  loading: boolean;
}) {
  //================================>
  // Demo mutation and secure backend-owned OAuth redirect
  //================================>
  const mock = useCreateMockLinkedInConnection();
  const connect = () => window.location.assign(getLinkedInAuthorizeUrl());
  return (
    <Box className="card">
      <Box className="card-head">
        <Box>
          <Typography variant="overline">Workspace</Typography>
          <Typography variant="h5">LinkedIn connection</Typography>
        </Box>
        <Box className="li-icon">
          <LinkedInIcon />
        </Box>
      </Box>
      {loading ? (
        <Box className="center">
          <CircularProgress size={24} />
        </Box>
      ) : connection ? (
        <Box className="connection-list">
          <Box className="connection">
            <Box className="avatar">{(connection.display_name ?? 'L')[0]}</Box>
            <Box className="grow">
              <Typography fontWeight={800}>
                {connection.display_name ?? 'LinkedIn member'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Connected · expires {new Date(connection.token_expires_at).toLocaleDateString()}
              </Typography>
            </Box>
            <Chip label="Active" color="success" size="small" variant="outlined" />
          </Box>
        </Box>
      ) : (
        <Box className="empty">
          <Typography color="text.secondary">
            Connect an account to schedule and publish securely.
          </Typography>
          <Button variant="contained" startIcon={<LinkedInIcon />} onClick={connect}>
            Connect LinkedIn
          </Button>
          <Button
            size="small"
            startIcon={<ScienceRoundedIcon />}
            disabled={mock.isPending}
            onClick={() => mock.mutate()}
          >
            Use demo account
          </Button>
        </Box>
      )}
    </Box>
  );
}
