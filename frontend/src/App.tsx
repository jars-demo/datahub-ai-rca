import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import Sidebar from './components/Sidebar';
import AboutPage from './pages/AboutPage';
import AssistantPage from './pages/AssistantPage';
import ConceptsPage from './pages/ConceptsPage';
import ConnectionsPage from './pages/ConnectionsPage';
import HomePage from './pages/HomePage';
import InvestigatePage from './pages/InvestigatePage';
import LineagePage from './pages/LineagePage';
import WorkshopPage from './pages/WorkshopPage';

export default function App() {
    return (
        <BrowserRouter>
            <div className="shell">
                <Sidebar />
                <main className="main">
                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/workshop" element={<WorkshopPage />} />
                        <Route path="/concepts" element={<ConceptsPage />} />
                        <Route path="/assistant" element={<AssistantPage />} />
                        <Route path="/investigate" element={<InvestigatePage />} />
                        <Route path="/lineage" element={<LineagePage />} />
                        <Route path="/connections" element={<ConnectionsPage />} />
                        <Route path="/about" element={<AboutPage />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}
