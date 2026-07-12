import { createBrowserRouter } from 'react-router'

import { HomePage } from '@/routes/home-page'
import { RootLayout } from '@/routes/root-layout'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [{ index: true, element: <HomePage /> }],
  },
])
