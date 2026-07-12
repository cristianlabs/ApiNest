import { createBrowserRouter, Navigate } from 'react-router'

import { LoginPage } from '@/routes/auth/login-page'
import { RegisterPage } from '@/routes/auth/register-page'
import { PublicOnlyRoute } from '@/routes/public-only-route'
import { RequireAuth } from '@/routes/require-auth'
import { RootLayout } from '@/routes/root-layout'
import { AcceptInvitationPage } from '@/features/organizations/accept-invitation-page'
import { OrganizationDetailPage } from '@/features/organizations/organization-detail-page'
import { OrganizationsListPage } from '@/features/organizations/organizations-list-page'
import { ProjectDetailPage } from '@/features/projects/project-detail-page'

export const router = createBrowserRouter([
  {
    element: <PublicOnlyRoute />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
    ],
  },
  {
    element: <RequireAuth />,
    children: [
      {
        path: '/',
        element: <RootLayout />,
        children: [
          { index: true, element: <Navigate to="/organizations" replace /> },
          { path: 'organizations', element: <OrganizationsListPage /> },
          { path: 'organizations/:orgId', element: <OrganizationDetailPage /> },
          { path: 'organizations/:orgId/projects/:projectId', element: <ProjectDetailPage /> },
        ],
      },
      { path: '/invitations/:token', element: <AcceptInvitationPage /> },
    ],
  },
])
