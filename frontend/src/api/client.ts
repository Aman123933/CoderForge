const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface RunRecord {
  id: string;
  prompt: string;
  status: string;
  created_at: string;
  total_latency_ms: number;
  retries_used: number;
  files_count: number;
  execution_success: boolean;
}

export interface PipelineResult {
  intent?: any;
  plan?: any;
  architecture?: any;
  project?: Record<string, string>;
  files?: Record<string, string>;
  manifest?: {
    entrypoint?: string;
    file_count?: number;
    files?: string[];
  };
  code?: string;
  review?: {
    summary?: string;
    issues?: Array<{
      severity: string;
      description: string;
      location: string;
    }>;
    recommendations?: string[];
  };
  attempts?: Array<{
    attempt: number;
    issues_count?: {
      critical: number;
      major: number;
      minor: number;
      total: number;
    };
  }>;
  retries_used?: number;
  execution?: {
    success: boolean;
    exit_code?: number;
    output?: string;
    stderr?: string;
    duration?: number;
    error?: string;
  };
  metrics?: {
    run_id: string;
    prompt: string;
    per_agent_latency_ms: Record<string, number>;
    total_latency_ms: number;
    llm_calls: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    retries_used: number;
    execution_success: boolean;
    files_generated: number;
  };
}

export async function runPrompt(prompt: string): Promise<{ run_id: string; result: PipelineResult }> {
  const res = await fetch(`${API_BASE_URL}/api/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Pipeline run failed (${res.status}): ${errorText}`);
  }

  return res.json();
}

export async function fetchRuns(): Promise<RunRecord[]> {
  const res = await fetch(`${API_BASE_URL}/api/runs?limit=30`);
  if (!res.ok) throw new Error("Failed to fetch runs");
  const data = await res.json();
  return data.runs || [];
}

export async function fetchRunById(id: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/runs/${id}`);
  if (!res.ok) throw new Error(`Run ${id} not found`);
  return res.json();
}

export async function fetchMetrics(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}
