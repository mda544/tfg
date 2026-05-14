import { useAuth } from "./auth/useAuth";
import App from "./App";
import AuthPage from "./auth/AuthPage";

export default function Root() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <App /> : <AuthPage />;
}