import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    apiUrl: process.env.BACKEND_URL || 'http://localhost:8080',
  });
}
