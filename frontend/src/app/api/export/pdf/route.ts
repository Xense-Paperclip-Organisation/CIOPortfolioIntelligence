/**
 * PDF export — proxy to FastAPI backend (reportlab-based, no Chromium required).
 * The Next.js rewrite in next.config.mjs would handle /api/* → backend, but
 * Next.js API routes take precedence over rewrites. We explicitly forward here
 * so the rewrite config stays clean and this file documents the intent.
 */
import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET() {
  const backend = process.env.BACKEND_URL || 'http://backend:8000';
  const upstreamUrl = `${backend}/api/export/pdf`;

  let upstreamRes: Response;
  try {
    upstreamRes = await fetch(upstreamUrl, { cache: 'no-store' });
  } catch (e: any) {
    return NextResponse.json(
      { error: 'backend unreachable', detail: e?.message },
      { status: 502 }
    );
  }

  if (!upstreamRes.ok) {
    const body = await upstreamRes.text();
    return NextResponse.json(
      { error: 'pdf generation failed', detail: body },
      { status: upstreamRes.status }
    );
  }

  const pdfBytes = await upstreamRes.arrayBuffer();
  return new NextResponse(pdfBytes, {
    status: 200,
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': 'inline; filename="cio-briefing.pdf"',
    },
  });
}
