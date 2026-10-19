# Troubleshooting

| Symptom | Fix |
|---|---|
| Sidebar says *DataHub not reachable* | DataHub isn't running, or GMS isn't on `http://localhost:8080`. Check `docker ps` and the DataHub card. |
| *Could not create an access token* | The UI URL is wrong, or the login changed. Create a token in DataHub (Settings → Access Tokens) and paste it. |
| *Never-expiring access tokens cannot be created* | Newer DataHub versions disallow them; the app already creates 90-day tokens. Update the app. |
| Pinecone seed waits a long time | A new serverless index takes up to a minute to become ready and searchable. |
| Langfuse seed: *rejected the key pair* | Public and secret key are from different projects, or the host is the wrong region. |
| DataHub seed: *Ingestion environment not found* | Run `make setup` (it creates `ingestion/.venv`). |
| Langfuse ingestion finds no traces | Seed Langfuse first; the recipe reads the last 8 days. |
| Lineage page is empty | Run the *Ingest into DataHub* step, then **Refresh**. |
| Agent: *model … isn't available* | Fix the model name on the LLM card; the test lists available models. |
| Agent answers without calling tools | The model doesn't support tool calling. Choose one that does. |
| DataHub containers keep restarting on a small machine | DataHub needs about 8 GB of free memory. Add swap or use a larger machine. |
| Remote machine: pages don't load locally | Forward ports 3300, 8300 and 9002. |
