import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemText,
  Typography,
  CircularProgress,
  Button,
} from "@mui/material";
import { Video } from "../types";

interface VideoListProps {
  videos: Video[] | null;
  isLoading: boolean;
  currentPage: number;
  onPageChange: (page: number) => void;
}

export function VideoList({ videos, isLoading, currentPage, onPageChange }: VideoListProps) {
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!videos || videos.length === 0) {
    return (
      <Typography variant="body2" sx={{ textAlign: 'center', p: 2 }}>
        No videos found.
      </Typography>
    );
  }

	// TODO add a button that says "load subtitle"
  return (
    <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #eee' }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>
        Processed Videos
      </Typography>
      <List>
        {videos.map((video) => (
          <ListItem key={video.id}>
            <ListItemText
              primary={video.videoId}
              secondary={`Source: ${video.videoSource} | Status: ${video.status}`}
            />
          </ListItem>
        ))}
      </List>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
        <Button
          variant="outlined"
          size="small"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 0}
        >
          Previous
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={() => onPageChange(currentPage + 1)}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}
