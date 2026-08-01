import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { Resident, Event, Reminder } from '../types';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_API_URL ?? '/api',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as any).auth?.token;
      if (token) headers.set('authorization', `Bearer ${token}`);
      return headers;
    },
  }),
  tagTypes: ['Resident', 'Event', 'Reminder'],
  endpoints: (builder) => ({
    getResidents: builder.query<Resident[], void>({
      query: () => '/residents',
      providesTags: [{ type: 'Resident', id: 'LIST' }],
    }),
    // 其他端點可依需求加入
  }),
});

export const { useGetResidentsQuery } = api;
