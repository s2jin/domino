import { AuthorizationRoute, PrivateRoute } from "@components/Routes";
import React from "react";
import { Route, Routes } from "react-router-dom";
import { ChatbotPage } from "../pages";

export const ChatbotRoutes: React.FC = () => {
  return (
    <Routes>
      <Route element={<PrivateRoute />}>
        <Route
          index
          element={
            <AuthorizationRoute>
              <ChatbotPage />
            </AuthorizationRoute>
          }
        />
      </Route>
    </Routes>
  );
};
