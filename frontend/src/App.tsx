import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AddDevicePage } from "./pages/AddDevicePage";
import { DeviceDetailPage } from "./pages/DeviceDetailPage";
import { DeviceListPage } from "./pages/DeviceListPage";

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="border-b border-gray-200 bg-white px-4 py-3 shadow-sm">
          <span className="font-semibold text-gray-800">SimDevice Manager</span>
        </nav>
        <Routes>
          <Route path="/" element={<DeviceListPage />} />
          <Route path="/devices/new" element={<AddDevicePage />} />
          <Route path="/devices/:id" element={<DeviceDetailPage />} />
        </Routes>
      </div>
    </Router>
  );
}
