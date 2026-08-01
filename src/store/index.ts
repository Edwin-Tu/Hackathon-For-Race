import { configureStore } from '@reduxjs/toolkit';
import { api } from './apiSlice';
import { videoApi } from './videoApi';

export const store = configureStore({
  reducer: {
    [api.reducerPath]: api.reducer,
    [videoApi.reducerPath]: videoApi.reducer,
    // 如需加入 auth reducer 可在此擴充
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware).concat(videoApi.middleware),
});

type RootState = ReturnType<typeof store.getState>;
export type { RootState };
