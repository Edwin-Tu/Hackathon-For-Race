import { configureStore } from '@reduxjs/toolkit';
import { api } from './apiSlice';
import { videoApi } from './videoApi';
import videoReducer from './videoSlice';

export const store = configureStore({
  reducer: {
    [api.reducerPath]: api.reducer,
    [videoApi.reducerPath]: videoApi.reducer,
    video: videoReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware).concat(videoApi.middleware),
});

type RootState = ReturnType<typeof store.getState>;
export type { RootState };
