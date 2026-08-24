import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const host = req.headers.get('host') || 'localhost:3000';
  const hostIp = host.split(':')[0];
  const apiUrl = `http://${hostIp}:8080`;
  // Derive the websocket URL from the API URL so it always points at the
  // same backend host, whether behind docker or running locally.
  const wsUrl = apiUrl.replace(/^http/, 'ws');

  return NextResponse.json({ apiUrl, wsUrl });
}
