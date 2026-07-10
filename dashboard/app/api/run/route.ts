import { spawn, spawnSync } from 'child_process';
import path from 'path';
import fs from 'fs';

export const dynamic = 'force-dynamic';

function getPythonInvocation() {
  const candidates = process.platform === 'win32'
    ? [
        { command: 'py', args: ['-3'] },
        { command: 'python', args: [] },
        { command: 'python3', args: [] },
      ]
    : [
        { command: 'python3', args: [] },
        { command: 'python', args: [] },
      ];

  for (const candidate of candidates) {
    const result = spawnSync(candidate.command, [...candidate.args, '--version'], { stdio: 'ignore' });
    if (result.status === 0) {
      return candidate;
    }
  }

  return process.platform === 'win32'
    ? { command: 'py', args: ['-3'] }
    : { command: 'python3', args: [] };
}

function resolveScraperDir(company: string) {
  const candidateRoots = [
    process.cwd(),
    path.resolve(process.cwd(), '..'),
    path.resolve(process.cwd(), 'dashboard'),
    path.resolve(process.cwd(), '..', 'dashboard'),
    path.resolve(process.cwd(), '..', '..'),
    path.resolve(process.cwd(), '..', '..', 'dashboard'),
  ];

  for (const candidateRoot of candidateRoots) {
    const scraperDir = path.join(candidateRoot, company, 'scraper');
    if (fs.existsSync(scraperDir)) {
      return scraperDir;
    }
  }

  return path.join(candidateRoots[0], company, 'scraper');
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const company = searchParams.get('company') || 'highsolar';
  const target = searchParams.get('target') || 'Kee';
  
  const scraperDir = resolveScraperDir(company);
  const python = getPythonInvocation();
  
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(`[SYSTEM] Starting workflow run for ${company} with target ${target}...\n`));
      
      const child = spawn(python.command, [...python.args, 'run_workflow.py', target], {
        cwd: scraperDir,
        env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONUTF8: '1' }
      });
      
      child.stdout.on('data', (data) => {
        controller.enqueue(encoder.encode(data.toString()));
      });
      
      child.stderr.on('data', (data) => {
        controller.enqueue(encoder.encode(`[STDERR] ${data.toString()}`));
      });
      
      child.on('close', (code) => {
        let leadsCount = 0;
        let rejectedCount = 0;
        
        try {
          const resultPath = path.join(scraperDir, 'filter_result.json');
          if (fs.existsSync(resultPath)) {
            const data = JSON.parse(fs.readFileSync(resultPath, 'utf8'));
            leadsCount = data.leads?.length || 0;
            rejectedCount = data.not_leads?.length || 0;
          }
        } catch (e) {
          console.error('Error reading filter result for history:', e);
        }
        
        // Append to run_history.json
        try {
          const historyPath = path.join(scraperDir, 'run_history.json');
          let history = [];
          if (fs.existsSync(historyPath)) {
            history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
          }
          const runId = `run_${Date.now()}`;
          const timestamp = new Date().toLocaleString('en-US', { timeZone: 'Asia/Bangkok' });
          history.unshift({
            id: runId,
            timestamp,
            target,
            status: code === 0 ? 'Success' : 'Failed',
            leadsCount,
            rejectedCount
          });
          fs.writeFileSync(historyPath, JSON.stringify(history.slice(0, 20), null, 2), 'utf8');

          // Copy filter_result.json to history_results/runId.json
          const resultPath = path.join(scraperDir, 'filter_result.json');
          if (fs.existsSync(resultPath)) {
            const historyDir = path.join(scraperDir, 'history_results');
            if (!fs.existsSync(historyDir)) {
              fs.mkdirSync(historyDir, { recursive: true });
            }
            fs.copyFileSync(resultPath, path.join(historyDir, `${runId}.json`));
          }
        } catch (e) {
          console.error('Error writing run history:', e);
        }
        
        controller.enqueue(encoder.encode(`\n[SYSTEM] Run complete. Process exited with code ${code}\n`));
        controller.close();
      });
      
      child.on('error', (err) => {
        controller.enqueue(encoder.encode(`[SYSTEM ERROR] Failed to start process: ${err.message}\n`));
        controller.close();
      });
    }
  });
  
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    }
  });
}
