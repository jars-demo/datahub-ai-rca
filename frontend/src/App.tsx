import { MagnifyingGlass, TreeStructure } from '@phosphor-icons/react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import Sidebar from './components/Sidebar';
import ComingSoonPage from './pages/ComingSoonPage';
import ConnectionsPage from './pages/ConnectionsPage';
import OverviewPage from './pages/OverviewPage';

export default function App() {
    return (
        <BrowserRouter>
            <div className="shell">
                <Sidebar />
                <main className="main">
                    <Routes>
                        <Route path="/" element={<OverviewPage />} />
                        <Route path="/connections" element={<ConnectionsPage />} />
                        <Route
                            path="/investigate"
                            element={
                                <ComingSoonPage
                                    title="Investigate"
                                    subtitle="Ask the root-cause agent a question."
                                    icon={MagnifyingGlass}
                                    description="Ask a question such as “Why did answer quality drop this week?” The agent traces Langfuse scores, prompt versions, Pinecone namespaces and DataHub lineage to identify the cause."
                                />
                            }
                        />
                        <Route
                            path="/lineage"
                            element={
                                <ComingSoonPage
                                    title="AI lineage"
                                    subtitle="One graph from source data to model output."
                                    icon={TreeStructure}
                                    description="A single lineage graph from source documents to Pinecone namespaces, Langfuse prompts and production traces, modeled in DataHub."
                                />
                            }
                        />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}
