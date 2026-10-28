import { Route, Routes } from 'react-router-dom';
import LoginPage from './pages/LoginPage.jsx';
import StudentHome from './pages/StudentHome.jsx';

// When merging into the existing ProtoLearn app, copy only these two <Route>s
// into its router and keep the site's own routes as they are.
export default function App() {
  return (
    <Routes>
      <Route path="/admin" element={<LoginPage />} />
      <Route path="/login" element={<StudentHome />} />
    </Routes>
  );
}
