import { NextRequest } from 'next/server';

// This API route acts as a proxy to the backend FastAPI server
// It helps avoid CORS issues by making the request server-to-server
export async function POST(req: NextRequest) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const body = await req.json();

  try {
    const response = await fetch(`${backendUrl}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return new Response(errorText, { 
        status: response.status,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Create a transform stream to pass data through
    const stream = response.body;

    return new Response(stream, {
      headers: {
        'Content-Type': 'application/x-ndjson',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error: any) {
    console.error('Proxy error:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

