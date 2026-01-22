import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./Home";
import History from "./History";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </BrowserRouter>
  );
}
