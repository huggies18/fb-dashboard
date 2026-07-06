import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { company, config } = body;
    
    if (!company || !config) {
      return NextResponse.json({ success: false, error: 'Missing company or config parameters' }, { status: 400 });
    }
    
    const rootDir = path.resolve(process.cwd(), '..');
    const configPath = path.join(rootDir, company, 'scraper', 'config.json');
    
    fs.writeFileSync(configPath, JSON.stringify(config, null, 4), 'utf8');
    
    return NextResponse.json({ success: true, message: 'Configuration saved successfully' });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
