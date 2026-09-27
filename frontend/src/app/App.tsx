import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { RequireRole } from "@/components/RequireRole";
import { LoginPage } from "@/features/auth/LoginPage";
import { DoctorDashboard } from "@/features/doctor/DoctorDashboard";
import { CaseDetailPage } from "@/features/doctor/CaseDetailPage";
import { ReviewerQueuePage } from "@/features/reviewer/ReviewerQueuePage";
import { ReviewerCasePage } from "@/features/reviewer/ReviewerCasePage";
import { UsersPage } from "@/features/admin/UsersPage";
import { AuditPage } from "@/features/admin/AuditPage";
import { ModelVersionsPage } from "@/features/admin/ModelVersionsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Layout />}>
        <Route
          path="/doctor"
          element={
            <RequireRole roles={["doctor", "admin"]}>
              <DoctorDashboard />
            </RequireRole>
          }
        />
        <Route
          path="/doctor/cases/:id"
          element={
            <RequireRole roles={["doctor", "admin"]}>
              <CaseDetailPage />
            </RequireRole>
          }
        />
        <Route
          path="/reviewer"
          element={
            <RequireRole roles={["senior_clinician", "admin"]}>
              <ReviewerQueuePage />
            </RequireRole>
          }
        />
        <Route
          path="/reviewer/cases/:id"
          element={
            <RequireRole roles={["senior_clinician", "admin"]}>
              <ReviewerCasePage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/users"
          element={
            <RequireRole roles={["admin"]}>
              <UsersPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/audit"
          element={
            <RequireRole roles={["admin"]}>
              <AuditPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/models"
          element={
            <RequireRole roles={["admin"]}>
              <ModelVersionsPage />
            </RequireRole>
          }
        />
        <Route path="/" element={<Navigate to="/doctor" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
