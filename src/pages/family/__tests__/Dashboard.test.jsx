import { render, screen } from '@testing-library/react';
import Dashboard from '../Dashboard';

jest.mock('../../hooks/useFamilyStats', () => ({
  useFamilyStats: () => ({ stats: { glucose: 100, heartRate: 70, unreadAlerts: 2 }, loading: false, error: null })
}));

test('renders dashboard stats', () => {
  render(<Dashboard />);
  expect(screen.getByText(/血糖/)).toBeInTheDocument();
  expect(screen.getByText('100 mg/dL')).toBeInTheDocument();
  expect(screen.getByText(/心率/)).toBeInTheDocument();
  expect(screen.getByText('70 bpm')).toBeInTheDocument();
});
