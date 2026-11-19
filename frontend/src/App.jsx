import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import DocumentDetail from './pages/DocumentDetail';
import AnalysisDetail from './pages/AnalysisDetail';
import ReviewQueue from './pages/ReviewQueue';
import AuditLedger from './pages/AuditLedger';
import Policies from './pages/Policies';
import PolicyDetail from './pages/PolicyDetail';
import Claims from './pages/Claims';
import NewClaim from './pages/NewClaim';
import ClaimDetail from './pages/ClaimDetail';

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="policies" element={<Policies />} />
              <Route path="policies/:id" element={<PolicyDetail />} />
              <Route path="claims" element={<Claims />} />
              <Route path="claims/new" element={<NewClaim />} />
              <Route path="claims/:id" element={<ClaimDetail />} />
              <Route
                path="documents"
                element={
                  <ProtectedRoute allowedRoles={['REVIEWER', 'ADMIN']}>
                    <Documents />
                  </ProtectedRoute>
                }
              />
              <Route
                path="documents/:id"
                element={
                  <ProtectedRoute allowedRoles={['REVIEWER', 'ADMIN']}>
                    <DocumentDetail />
                  </ProtectedRoute>
                }
              />
              <Route
                path="analyses/:id"
                element={
                  <ProtectedRoute allowedRoles={['REVIEWER', 'ADMIN']}>
                    <AnalysisDetail />
                  </ProtectedRoute>
                }
              />
              <Route
                path="reviews"
                element={
                  <ProtectedRoute allowedRoles={['REVIEWER', 'ADMIN']}>
                    <ReviewQueue />
                  </ProtectedRoute>
                }
              />
              <Route
                path="audit"
                element={
                  <ProtectedRoute allowedRoles={['REVIEWER', 'ADMIN']}>
                    <AuditLedger />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}
