/**
 * Custom API route for guided session start
 * Handles long-running OpenAI requests with extended timeout
 */
import { NextRequest, NextResponse } from 'next/server';

// Increase timeout for this route to 60 seconds
// This allows OpenAI API calls to complete without timing out
export const maxDuration = 60;

export async function POST(request: NextRequest) {
  try {
    // Parse the incoming request body
    const body = await request.json();
    
    // Forward the request to the FastAPI backend
    // Use a longer timeout (30 seconds) for the fetch
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    
    const response = await fetch('http://127.0.0.1:8000/api/py/guided/start-session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    // Forward the response back to the client
    const data = await response.json();
    
    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to start session' },
        { status: response.status }
      );
    }
    
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error in start-session proxy:', error);
    
    // Handle timeout specifically
    if (error.name === 'AbortError') {
      return NextResponse.json(
        { error: 'Request timed out. The AI is taking longer than expected. Please try again.' },
        { status: 504 }
      );
    }
    
    // Handle other errors
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

