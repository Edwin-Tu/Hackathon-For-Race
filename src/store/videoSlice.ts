// src/store/videoSlice.ts
import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

export interface ActiveTask {
  residentId: string;
  taskId: string;
}

interface VideoState {
  activeTask: ActiveTask | null;
}

const initialState: VideoState = {
  activeTask: null,
};

export const videoSlice = createSlice({
  name: 'video',
  initialState,
  reducers: {
    setActiveTask: (state, action: PayloadAction<ActiveTask>) => {
      state.activeTask = action.payload;
    },
    clearActiveTask: (state) => {
      state.activeTask = null;
    },
  },
});

export const { setActiveTask, clearActiveTask } = videoSlice.actions;

// Selector
export const selectActiveTask = (state: { video: VideoState }) => state.video.activeTask;

export default videoSlice.reducer;
