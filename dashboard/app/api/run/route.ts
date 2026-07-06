import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const company = searchParams.get('company') || 'highsolar';
  const target = searchParams.get('target') || 'Kee';
  
  const rootDir = path.resolve(process.cwd(), '..');
  const scraperDir = path.join(rootDir, company, 'scraper');
  
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(`[SYSTEM] Starting workflow run for ${company} with target ${target}...\n`));
      
      const pythonCommand = process.platform === 'win32' ? 'py' : 'python3';
      const child = spawn(pythonCommand, ['run_workflow.py', target], {
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
