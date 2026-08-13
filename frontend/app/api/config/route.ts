import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const host = req.headers.get('host') || 'localhost:3000';
  const hostIp = host.split(':')[0];
  const apiUrl = `http://${hostIp}:8080`;

  return NextResponse.json({ apiUrl });
}
