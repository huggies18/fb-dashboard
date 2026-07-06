import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const company = searchParams.get('company') || 'highsolar';
  
  try {
    const rootDir = path.resolve(process.cwd(), '..');
    const scraperDir = path.join(rootDir, company, 'scraper');
    
    // Read config
    const configPath = path.join(scraperDir, 'config.json');
    let config = {};
    if (fs.existsSync(configPath)) {
      config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    }
    
    // Read filter results
    const runId = searchParams.get('runId');
    let resultPath = path.join(scraperDir, 'filter_result.json');
    if (runId && runId !== 'latest') {
      resultPath = path.join(scraperDir, 'history_results', `${runId}.json`);
    }
    
    let leads = [];
    let notLeads = [];
    let lastUpdated = '';
    if (fs.existsSync(resultPath)) {
      try {
        const results = JSON.parse(fs.readFileSync(resultPath, 'utf8'));
        leads = results.leads || [];
        notLeads = results.not_leads || [];
        lastUpdated = results.timestamp || '';
      } catch (e) {
        console.error('Error parsing filter results:', e);
      }
    }
    
    // Check if log file exists to read any final progress
    const logPath = path.join(scraperDir, 'scrape_all.log');
    let isRunning = false;
    // Simple way to determine if running: check if a workflow process might be running (optional background poll, or let api/run manage state).
    
    // Read run history
    const historyPath = path.join(scraperDir, 'run_history.json');
    let history = [];
    if (fs.existsSync(historyPath)) {
      try {
        history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
      } catch (e) {
        console.error('Error parsing run history:', e);
      }
    }
    
    return NextResponse.json({
      config,
      leads,
      notLeads,
      lastUpdated,
      history,
      success: true
    });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const company = searchParams.get('company') || 'highsolar';
  const id = searchParams.get('id');
  
  try {
    const rootDir = path.resolve(process.cwd(), '..');
    const scraperDir = path.join(rootDir, company, 'scraper');
    const historyPath = path.join(scraperDir, 'run_history.json');
    
    if (!fs.existsSync(historyPath)) {
      return NextResponse.json({ success: true, message: 'No history file found' });
    }
    
    let history = [];
    try {
      history = JSON.parse(fs.readFileSync(historyPath, 'utf8'));
    } catch (e) {
      console.error('Error parsing run history:', e);
    }
    
    if (id === 'all') {
      // Clear entire history
      fs.writeFileSync(historyPath, JSON.stringify([], null, 2), 'utf8');
      
      // Clean history_results directory if it exists
      const historyDir = path.join(scraperDir, 'history_results');
      if (fs.existsSync(historyDir)) {
        fs.rmSync(historyDir, { recursive: true, force: true });
      }
      history = [];
    } else if (id) {
      // Remove specific entry
      history = history.filter((run: any) => run.id !== id);
      fs.writeFileSync(historyPath, JSON.stringify(history, null, 2), 'utf8');
      
      // Also delete the saved file in history_results
      const detailPath = path.join(scraperDir, 'history_results', `${id}.json`);
      if (fs.existsSync(detailPath)) {
        fs.unlinkSync(detailPath);
      }
    }
    
    return NextResponse.json({ success: true, history });
  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
