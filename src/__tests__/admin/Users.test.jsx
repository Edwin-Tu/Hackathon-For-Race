import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Users from '../Users';

// Mock fetch 全局
global.fetch = jest.fn();

const mockUsers = [{ id: '1', username: 'admin1', role: 'ADMIN' }];

beforeEach(() => {
  fetch.mockImplementation((url, opts) => {
    if (url === '/api/admin/users' && (!opts || opts.method === 'GET')) {
      return Promise.resolve({ json: () => Promise.resolve(mockUsers) });
    }
    return Promise.resolve({});
  });
});

test('renders user table', async () => {
  render(<Users />);
  await waitFor(() => expect(screen.getByText('admin1')).toBeInTheDocument());
});

test('opens edit dialog', async () => {
  render(<Users />);
  await waitFor(() => screen.getByText('admin1'));
  const editBtn = screen.getAllByLabelText('edit')[0]; // MUI IconButton provides aria-label automatically
  fireEvent.click(editBtn);
  expect(screen.getByText('編輯使用者')).toBeInTheDocument();
});
