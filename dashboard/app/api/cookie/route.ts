import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const company = searchParams.get('company') || 'highsolar';
  
  try {
    const rootDir = path.resolve(process.cwd(), '..');
    const cookiePath = path.join(rootDir, company, 'scraper', 'fb_session.json');
    
    let cookiesContent = '{\n  "cookies": [],\n  "last_updated": ""\n}';
    if (fs.existsSync(cookiePath)) {
      cookiesContent = fs.readFileSync(cookiePath, 'utf8');
    }
    
    return NextResponse.json({ success: true, cookiesContent });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { company, rawJson } = body;
    
    if (!company || !rawJson) {
      return NextResponse.json({ success: false, error: 'Missing parameters' }, { status: 400 });
    }
    
    let parsedJson;
    try {
      parsedJson = JSON.parse(rawJson);
    } catch (e: any) {
      return NextResponse.json({ success: false, error: 'Invalid JSON format: ' + e.message }, { status: 400 });
    }
    
    // Normalize format
    let finalObject: any = {};
    if (Array.isArray(parsedJson)) {
      finalObject = {
        cookies: parsedJson,
        last_updated: new Date().toISOString().replace('T', ' ').substring(0, 19)
      };
    } else if (parsedJson.cookies && Array.isArray(parsedJson.cookies)) {
      finalObject = {
        ...parsedJson,
        last_updated: parsedJson.last_updated || new Date().toISOString().replace('T', ' ').substring(0, 19)
      };
    } else {
      return NextResponse.json({ success: false, error: 'JSON must contain a list of cookies or a "cookies" field' }, { status: 400 });
    }
    
    const rootDir = path.resolve(process.cwd(), '..');
    const cookiePath = path.join(rootDir, company, 'scraper', 'fb_session.json');
    
    fs.writeFileSync(cookiePath, JSON.stringify(finalObject, null, 2), 'utf8');
    
    return NextResponse.json({ success: true, message: 'Cookies updated successfully', cookiesContent: JSON.stringify(finalObject, null, 2) });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
