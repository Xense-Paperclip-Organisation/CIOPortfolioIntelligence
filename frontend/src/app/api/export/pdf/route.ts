import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET(req: Request) {
  // Lazy-import so dev / build doesn't choke if puppeteer's Chromium isn't installed
  // at build time.  At runtime, the docker image includes the Chromium deps.
  let puppeteer: typeof import('puppeteer');
  try {
    puppeteer = await import('puppeteer');
  } catch (e: any) {
    return NextResponse.json({ error: 'puppeteer unavailable', detail: e?.message }, { status: 500 });
  }
  const url = new URL(req.url);
  const target = `${url.origin}/?print=1`;
  try {
    const browser = await puppeteer.launch({
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
      headless: true
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 1800, deviceScaleFactor: 1.5 });
    await page.goto(target, { waitUntil: 'networkidle0', timeout: 60_000 });
    const pdf = await page.pdf({
      format: 'A4',
      printBackground: true,
      margin: { top: '12mm', right: '10mm', bottom: '12mm', left: '10mm' }
    });
    await browser.close();
    return new NextResponse(pdf, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'inline; filename="cio-briefing.pdf"'
      }
    });
  } catch (e: any) {
    return NextResponse.json({ error: 'pdf generation failed', detail: e?.message }, { status: 500 });
  }
}
