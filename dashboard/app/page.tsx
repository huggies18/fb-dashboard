'use strict';
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Settings, Play, Shield, Key, AlertTriangle, CheckCircle, XCircle, 
  RefreshCw, Upload, Eye, Cpu, Database, Clipboard, Trash2, Plus, History,
  Sun, Moon, Download
} from 'lucide-react';

interface TelegramTarget {
  name: string;
  chat_id: number;
  bot_token: string;
}

interface Config {
  groups: string[];
  keywords: string[];
  min_comment_length: number;
  min_scrolls: number;
  max_scrolls: number;
  min_delay: number;
  max_delay: number;
  headless: boolean;
  telegram_targets?: TelegramTarget[];
}

interface Lead {
  url: string;
  message: string;
  group: string;
  time?: string;
  scraped_at: string;
  score: number;
  is_lead: boolean;
  reason: string;
  contact?: string;
}

const defaultTargetsMap = {
  highsolar: [
    { name: 'Kee', chat_id: 8868315905, bot_token: '8662942478:AAFAPhgEC4WI6lM6FCdsQKr7h_o0gbavPgw' },
    { name: 'Tibodin', chat_id: 6780942246, bot_token: '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw' },
    { name: 'Nick', chat_id: 8698062232, bot_token: '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw' },
    { name: 'Noty', chat_id: 6780942246, bot_token: '8641112117:AAFokLi4gAvfqSUPjBz2AqUyGceAsX8M5CE' },
    { name: 'Tibodin2', chat_id: 6780942246, bot_token: '8690841708:AAHAtvAFc2SYGHVubVGq1DEAyPpmyvcguY8' }
  ],
  c1: [
    { name: 'Tibodin', chat_id: 6780942246, bot_token: '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw' },
    { name: 'Nick', chat_id: 8698062232, bot_token: '8774902841:AAFveLJDs-Bf02cPkBhZVPU5JBw_sdLIhNw' },
    { name: 'Noty', chat_id: 6780942246, bot_token: '8641111669:AAEf倪9V_k_82gBScTPsp8yncksM5CE' },
    { name: 'Kee', chat_id: 8868315905, bot_token: '8662942478:AAFAPhgEC4WI6lM6FCdsQKr7h_o0gbavPgw' }
  ]
};

export default function Home() {
  const [company, setCompany] = useState<'highsolar' | 'c1'>('highsolar');
  const [target, setTarget] = useState<string>('Kee');
  const [config, setConfig] = useState<Config>({
    groups: [],
    keywords: [],
    min_comment_length: 10,
    min_scrolls: 5,
    max_scrolls: 25,
    min_delay: 5,
    max_delay: 15,
    headless: true,
    telegram_targets: []
  });
  const [history, setHistory] = useState<any[]>([]);
  
  const [newGroup, setNewGroup] = useState('');
  const [newKeyword, setNewKeyword] = useState('');
  const [cookieText, setCookieText] = useState('');
  
  const [leads, setLeads] = useState<Lead[]>([]);
  const [notLeads, setNotLeads] = useState<Lead[]>([]);
  const [lastUpdated, setLastUpdated] = useState('');
  const [leadFilter, setLeadFilter] = useState<'all' | 'leads' | 'rejected'>('all');
  
  const [logs, setLogs] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState('');
  
  // Custom states
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [historyLeads, setHistoryLeads] = useState<Lead[] | null>(null);
  const [historyNotLeads, setHistoryNotLeads] = useState<Lead[] | null>(null);
  const [historyLastUpdated, setHistoryLastUpdated] = useState('');
  
  const [isThemeLight, setIsThemeLight] = useState(false);
  const [isManagingTargets, setIsManagingTargets] = useState(false);
  const [newTargetName, setNewTargetName] = useState('');
  const [newTargetChatId, setNewTargetChatId] = useState('');
  const [newTargetBotToken, setNewTargetBotToken] = useState('');
  
  const consoleRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    fetchStatus();
    fetchCookies();
  }, [company]);

  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    if (isThemeLight) {
      document.body.classList.add('light');
    } else {
      document.body.classList.remove('light');
    }
  }, [isThemeLight]);

  const fetchStatus = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/status?company=${company}`);
      const data = await res.json();
      if (data.success) {
        let activeConfig = data.config || {};
        // If config does not have telegram_targets, fill with default targets
        if (!activeConfig.telegram_targets || activeConfig.telegram_targets.length === 0) {
          activeConfig.telegram_targets = defaultTargetsMap[company];
          // Proactively save it back so config.json is populated
          await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company, config: activeConfig })
          });
        }
        
        setConfig(activeConfig);
        setLeads(data.leads || []);
        setNotLeads(data.notLeads || []);
        setLastUpdated(data.lastUpdated || '');
        setHistory(data.history || []);
        
        // Only reset history view selections when company changes (not on every fetchStatus call)
        // We use a functional update to avoid stale closure issues
        setSelectedRunId(prev => {
          // If company changes, prev selectedRunId won't be in new history — clear it
          const newHistory: any[] = data.history || [];
          if (prev && !newHistory.some((r: any) => r.id === prev)) {
            setHistoryLeads(null);
            setHistoryNotLeads(null);
            return null;
          }
          return prev;
        });
        
        // Select first target from list by default if available
        if (activeConfig.telegram_targets && activeConfig.telegram_targets.length > 0) {
          setTarget(activeConfig.telegram_targets[0].name);
        }
      }
    } catch (e) {
      console.error(e);
      setStatusMessage('Error loading status data');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchRunHistoryDetail = async (runId: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/status?company=${company}&runId=${runId}`);
      const data = await res.json();
      if (data.success) {
        setHistoryLeads(data.leads || []);
        setHistoryNotLeads(data.notLeads || []);
        setHistoryLastUpdated(data.lastUpdated || '');
        setSelectedRunId(runId);
      } else {
        alert('Failed to load run details: ' + data.error);
      }
    } catch (e: any) {
      alert('Error loading run details: ' + e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const showLatestResults = () => {
    setSelectedRunId(null);
    setHistoryLeads(null);
    setHistoryNotLeads(null);
  };

  const deleteRunHistory = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(id === 'all' ? 'Are you sure you want to clear all history?' : 'Are you sure you want to delete this run history?')) return;
    
    try {
      const res = await fetch(`/api/status?company=${company}&id=${id}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (data.success) {
        setHistory(data.history || []);
        if (id === 'all' || selectedRunId === id) {
          showLatestResults();
        }
      } else {
        alert('Failed to delete history: ' + data.error);
      }
    } catch (err: any) {
      alert('Error: ' + err.message);
    }
  };

  const fetchCookies = async () => {
    try {
      const res = await fetch(`/api/cookie?company=${company}`);
      const data = await res.json();
      if (data.success) {
        setCookieText(data.cookiesContent);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const saveConfig = async (updatedConfig = config) => {
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company, config: updatedConfig })
      });
      const data = await res.json();
      if (data.success) {
        setStatusMessage('Configuration saved successfully!');
        setTimeout(() => setStatusMessage(''), 3000);
      } else {
        setStatusMessage('Failed to save configuration: ' + data.error);
      }
    } catch (e: any) {
      setStatusMessage('Error: ' + e.message);
    }
  };

  const saveCookies = async () => {
    try {
      const res = await fetch('/api/cookie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company, rawJson: cookieText })
      });
      const data = await res.json();
      if (data.success) {
        setCookieText(data.cookiesContent);
        setStatusMessage('Cookies updated successfully!');
        setTimeout(() => setStatusMessage(''), 3000);
      } else {
        alert('Failed to save cookies: ' + data.error);
      }
    } catch (e: any) {
      alert('Error updating cookies: ' + e.message);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target?.result;
      if (typeof result === 'string') {
        setCookieText(result);
      }
    };
    reader.readAsText(file);
  };

  const runScraper = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setLogs(['[SYSTEM] Initializing scraper execution stream...']);
    
    try {
      const response = await fetch(`/api/run?company=${company}&target=${target}`);
      if (!response.body) {
        throw new Error('Readable stream not supported');
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        // Split logs by line and append
        setLogs(prev => [...prev, ...chunk.split('\n').filter(Boolean)]);
      }
    } catch (e: any) {
      setLogs(prev => [...prev, `[SYSTEM ERROR] ${e.message}`]);
    } finally {
      setIsRunning(false);
      fetchStatus(); // Refresh results when complete
    }
  };

  const addGroup = () => {
    if (!newGroup.trim()) return;
    const updated = { ...config, groups: [...config.groups, newGroup.trim()] };
    setConfig(updated);
    saveConfig(updated);
    setNewGroup('');
  };

  const removeGroup = (index: number) => {
    const updatedGroups = [...config.groups];
    updatedGroups.splice(index, 1);
    const updated = { ...config, groups: updatedGroups };
    setConfig(updated);
    saveConfig(updated);
  };

  const addKeyword = () => {
    if (!newKeyword.trim()) return;
    const updated = { ...config, keywords: [...config.keywords, newKeyword.trim()] };
    setConfig(updated);
    saveConfig(updated);
    setNewKeyword('');
  };

  const removeKeyword = (index: number) => {
    const updatedKeywords = [...config.keywords];
    updatedKeywords.splice(index, 1);
    const updated = { ...config, keywords: updatedKeywords };
    setConfig(updated);
    saveConfig(updated);
  };

  const updateNumericSetting = (key: keyof Config, val: number | boolean) => {
    const updated = { ...config, [key]: val };
    setConfig(updated);
    saveConfig(updated);
  };

  const filteredPosts = () => {
    const activeLeads = historyLeads !== null ? historyLeads : leads;
    const activeNotLeads = historyNotLeads !== null ? historyNotLeads : notLeads;
    if (leadFilter === 'leads') return activeLeads;
    if (leadFilter === 'rejected') return activeNotLeads;
    return [...activeLeads, ...activeNotLeads].sort((a, b) => b.score - a.score);
  };

  const exportToCSV = () => {
    const posts = filteredPosts();
    if (posts.length === 0) {
      alert('No data to export');
      return;
    }

    const headers = ['Group', 'Score', 'Status', 'URL', 'Message', 'Reason', 'Contact', 'Scraped At'];
    const csvRows = [headers.join(',')];

    for (const post of posts) {
      const status = post.is_lead ? 'Lead' : 'Rejected';
      const values = [
        post.group || '',
        post.score.toString(),
        status,
        post.url || '',
        post.message || '',
        post.reason || '',
        post.contact || '',
        post.scraped_at || ''
      ];

      const escapedValues = values.map(val => {
        const escaped = val.replace(/"/g, '""');
        return `"${escaped}"`;
      });
      csvRows.push(escapedValues.join(','));
    }

    const csvContent = "\uFEFF" + csvRows.join('\n'); // add BOM for Excel Thai language support
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    const filename = `${company}_scraped_posts_${leadFilter}_${new Date().toISOString().slice(0, 10)}.csv`;
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '40px 20px' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: 700, letterSpacing: '-0.5px', marginBottom: '8px' }}>
            <span style={{ color: 'var(--primary)' }}>FB Bot</span> Admin Dashboard
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Configure, run, and monitor automated scraping campaigns</p>
        </div>
        
        {/* Switchers */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Theme Switcher Button */}
          <button 
            onClick={() => setIsThemeLight(!isThemeLight)}
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              borderRadius: '12px',
              padding: '12px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.1)',
              transition: 'all 0.2s'
            }}
            title={isThemeLight ? "Switch to Dark Mode" : "Switch to Light Mode"}
          >
            {isThemeLight ? <Moon size={18} /> : <Sun size={18} />}
          </button>

          {/* Company Switcher */}
          <div className="glass-panel" style={{ display: 'flex', padding: '4px', borderRadius: '12px' }}>
            <button 
              onClick={() => setCompany('highsolar')}
              style={{
                background: company === 'highsolar' ? 'var(--primary)' : 'none',
                color: company === 'highsolar' ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              HighSolar Scraper
            </button>
            <button 
              onClick={() => setCompany('c1')}
              style={{
                background: company === 'c1' ? 'var(--primary)' : 'none',
                color: company === 'c1' ? '#fff' : 'var(--text-secondary)',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              C1 Scraper
            </button>
          </div>
        </div>
      </header>

      {statusMessage && (
        <div style={{
          background: 'var(--bg-tag)',
          border: '1px solid var(--primary)',
          color: 'var(--text-tag)',
          padding: '12px 20px',
          borderRadius: '8px',
          marginBottom: '24px',
          fontSize: '14px',
          fontWeight: 500
        }}>
          {statusMessage}
        </div>
      )}

      {/* Main Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '24px' }}>
        
        {/* Left Side: Parameters, settings & Cookie Manager */}
        <div style={{ gridColumn: 'span 5', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Bot Execution Controller */}
          <section className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
              <Cpu size={20} style={{ color: 'var(--primary)' }} />
              <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Bot Execution Control</h2>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    Telegram Target Alert User
                  </label>
                  <button 
                    onClick={() => setIsManagingTargets(!isManagingTargets)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--primary)',
                      fontSize: '11px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: 0
                    }}
                  >
                    <Settings size={12} />
                    {isManagingTargets ? 'Close Manager' : 'Manage Targets'}
                  </button>
                </div>

                {!isManagingTargets ? (
                  <select 
                    value={target} 
                    onChange={(e) => setTarget(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    {(config.telegram_targets || defaultTargetsMap[company] || []).map((t) => (
                      <option key={t.name} value={t.name}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '6px' }}>
                    <div style={{ maxHeight: '120px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {(config.telegram_targets || defaultTargetsMap[company] || []).map((t, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', padding: '6px 8px', background: 'rgba(0,0,0,0.15)', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                          <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <span style={{ fontWeight: 600 }}>{t.name}</span>
                            <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>ID: {t.chat_id}</span>
                          </div>
                          <button 
                            onClick={() => {
                              const updatedTargets = (config.telegram_targets || defaultTargetsMap[company] || []).filter((_, i) => i !== idx);
                              const updated = { ...config, telegram_targets: updatedTargets };
                              setConfig(updated);
                              saveConfig(updated);
                            }}
                            style={{ background: 'none', border: 'none', color: 'var(--error)', cursor: 'pointer' }}
                            title="Delete Target"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      ))}
                    </div>
                    
                    <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                        <input 
                          type="text" 
                          placeholder="Name (e.g. Nick)" 
                          value={newTargetName} 
                          onChange={(e) => setNewTargetName(e.target.value)}
                          style={{ padding: '6px 10px', fontSize: '12px' }}
                        />
                        <input 
                          type="text" 
                          placeholder="Chat ID (e.g. 1234)" 
                          value={newTargetChatId} 
                          onChange={(e) => setNewTargetChatId(e.target.value)}
                          style={{ padding: '6px 10px', fontSize: '12px' }}
                        />
                      </div>
                      <input 
                        type="text" 
                        placeholder="Bot Token" 
                        value={newTargetBotToken} 
                        onChange={(e) => setNewTargetBotToken(e.target.value)}
                        style={{ padding: '6px 10px', fontSize: '12px', width: '100%' }}
                      />
                      <button 
                        className="btn btn-secondary"
                        onClick={() => {
                          if (!newTargetName || !newTargetChatId || !newTargetBotToken) {
                            alert('Please fill out all target fields.');
                            return;
                          }
                          const newTarget = {
                            name: newTargetName.trim(),
                            chat_id: parseInt(newTargetChatId.trim()) || 0,
                            bot_token: newTargetBotToken.trim()
                          };
                          const currentTargets = config.telegram_targets || defaultTargetsMap[company] || [];
                          const updatedTargets = [...currentTargets, newTarget];
                          const updated = { ...config, telegram_targets: updatedTargets };
                          setConfig(updated);
                          saveConfig(updated);
                          setNewTargetName('');
                          setNewTargetChatId('');
                          setNewTargetBotToken('');
                        }}
                        style={{ padding: '8px', fontSize: '12px', width: '100%' }}
                      >
                        <Plus size={14} /> Add Alert User
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <button 
                className="btn btn-primary" 
                onClick={runScraper}
                disabled={isRunning}
                style={{ width: '100%', padding: '14px', display: 'flex', gap: '8px', fontSize: '15px' }}
              >
                {isRunning ? (
                  <>
                    <RefreshCw className="animate-spin" size={18} />
                    Scraping in progress...
                  </>
                ) : (
                  <>
                    <Play size={18} />
                    Run Scraper Now
                  </>
                )}
              </button>
            </div>
          </section>

          {/* Run History Card */}
          <section className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <History size={20} style={{ color: 'var(--primary)' }} />
                <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Run History</h2>
              </div>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                {selectedRunId && (
                  <button 
                    onClick={showLatestResults}
                    style={{
                      background: 'rgba(99, 102, 241, 0.15)',
                      border: '1px solid var(--primary)',
                      color: 'var(--primary)',
                      fontSize: '11px',
                      padding: '4px 10px',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      fontWeight: 600
                    }}
                  >
                    Show Latest
                  </button>
                )}
                {history.length > 0 && (
                  <button 
                    onClick={(e) => deleteRunHistory('all', e)}
                    className="btn-clear-all"
                    title="Clear All History"
                  >
                    <Trash2 size={12} style={{ pointerEvents: 'none' }} /> Clear All
                  </button>
                )}
              </div>
            </div>
            <div style={{ maxHeight: '200px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {history.map((run, idx) => {
                const isSelected = selectedRunId === run.id;
                return (
                  <div 
                    key={idx} 
                    onClick={() => run.id && fetchRunHistoryDetail(run.id)}
                    style={{ 
                      background: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'rgba(255,255,255,0.02)', 
                      padding: '10px 12px', 
                      borderRadius: '8px', 
                      border: isSelected ? '1px solid var(--primary)' : '1px solid rgba(255,255,255,0.04)', 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center', 
                      fontSize: '13px',
                      cursor: run.id ? 'pointer' : 'default',
                      transition: 'all 0.2s'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                        Target: {run.target} {isSelected && <span style={{ fontSize: '10px', color: 'var(--primary)', marginLeft: '6px' }}>(Viewing)</span>}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>{run.timestamp}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ 
                          fontSize: '11px', 
                          background: run.status === 'Success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                          color: run.status === 'Success' ? 'var(--success)' : 'var(--error)',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontWeight: 600
                        }}>
                          {run.status}
                        </span>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                          🟢 {run.leadsCount} | 🔴 {run.rejectedCount}
                        </div>
                      </div>
                      {run.id && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteRunHistory(run.id, e);
                          }}
                          className="run-history-delete"
                          title="Delete Run"
                        >
                          <Trash2 size={13} style={{ pointerEvents: 'none' }} />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
              {history.length === 0 && (
                <div style={{ color: 'var(--text-muted)', fontSize: '12px', textAlign: 'center', padding: '20px 0' }}>
                  No previous run records found
                </div>
              )}
            </div>
          </section>

          {/* Settings Panel */}
          <section className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
              <Settings size={20} style={{ color: 'var(--primary)' }} />
              <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Parameters Config</h2>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              {/* Group IDs Manager */}
              <div>
                <h3 style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Facebook Group IDs ({config.groups.length})
                </h3>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                  <input 
                    type="text" 
                    placeholder="Enter Group ID" 
                    value={newGroup}
                    onChange={(e) => setNewGroup(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addGroup()}
                    style={{ flex: 1 }}
                  />
                  <button className="btn btn-secondary" onClick={addGroup} style={{ padding: '10px' }}>
                    <Plus size={18} />
                  </button>
                </div>
                <div className="tag-container">
                  {config.groups.map((g, idx) => (
                    <span key={g} className="tag">
                      {g}
                      <button className="tag-remove" onClick={() => removeGroup(idx)}>&times;</button>
                    </span>
                  ))}
                  {config.groups.length === 0 && <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>No groups defined</span>}
                </div>
              </div>

              {/* Keywords Tag Manager */}
              <div>
                <h3 style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Search Target Keywords ({config.keywords.length})
                </h3>
                <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                  <input 
                    type="text" 
                    placeholder="Enter keyword" 
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
                    style={{ flex: 1 }}
                  />
                  <button className="btn btn-secondary" onClick={addKeyword} style={{ padding: '10px' }}>
                    <Plus size={18} />
                  </button>
                </div>
                <div className="tag-container" style={{ maxHeight: '150px', overflowY: 'auto' }}>
                  {config.keywords.map((kw, idx) => (
                    <span key={kw} className="tag">
                      {kw}
                      <button className="tag-remove" onClick={() => removeKeyword(idx)}>&times;</button>
                    </span>
                  ))}
                  {config.keywords.length === 0 && <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>No keywords defined</span>}
                </div>
              </div>

              {/* Numerical Options */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Min Mouse Scrolls
                  </label>
                  <input 
                    type="number" 
                    value={config.min_scrolls || 0}
                    onChange={(e) => updateNumericSetting('min_scrolls', parseInt(e.target.value) || 0)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Max Mouse Scrolls
                  </label>
                  <input 
                    type="number" 
                    value={config.max_scrolls || 0}
                    onChange={(e) => updateNumericSetting('max_scrolls', parseInt(e.target.value) || 0)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Min Comment Len
                  </label>
                  <input 
                    type="number" 
                    value={config.min_comment_length}
                    onChange={(e) => updateNumericSetting('min_comment_length', parseInt(e.target.value) || 0)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Min Delay (sec)
                  </label>
                  <input 
                    type="number" 
                    value={config.min_delay}
                    onChange={(e) => updateNumericSetting('min_delay', parseInt(e.target.value) || 0)}
                    style={{ width: '100%' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Max Delay (sec)
                  </label>
                  <input 
                    type="number" 
                    value={config.max_delay}
                    onChange={(e) => updateNumericSetting('max_delay', parseInt(e.target.value) || 0)}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              {/* Headless Toggle */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.1)', padding: '12px', borderRadius: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 500 }}>Run Headless Playwright</span>
                <input 
                  type="checkbox" 
                  checked={config.headless}
                  onChange={(e) => updateNumericSetting('headless', e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
              </div>

            </div>
          </section>

          {/* Cookie Manager */}
          <section className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Key size={20} style={{ color: 'var(--primary)' }} />
                <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Cookie Session Manager</h2>
              </div>
              <label className="btn btn-secondary" style={{ fontSize: '12px', padding: '6px 12px', gap: '4px', cursor: 'pointer' }}>
                <Upload size={12} />
                Upload JSON
                <input type="file" accept=".json" onChange={handleFileUpload} style={{ display: 'none' }} />
              </label>
            </div>

            <div>
              <textarea 
                value={cookieText}
                onChange={(e) => setCookieText(e.target.value)}
                placeholder="Paste cookies JSON array or session object here..."
                style={{ width: '100%', height: '150px', fontFamily: 'monospace', fontSize: '12px', marginBottom: '12px', resize: 'vertical' }}
              />
              <button className="btn btn-primary" onClick={saveCookies} style={{ width: '100%' }}>
                Update Cookie Session File
              </button>
            </div>
          </section>

        </div>

        {/* Right Side: Log Stream View and Scraped Lead Results Grid */}
        <div style={{ gridColumn: 'span 7', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Stream Log Viewer */}
          <section className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Eye size={20} style={{ color: 'var(--primary)' }} />
                <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Real-Time Scraper Logs</h2>
              </div>
              {isRunning && (
                <span style={{ fontSize: '12px', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--success)', padding: '4px 10px', borderRadius: '20px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)', display: 'inline-block', animation: 'pulse 1.5s infinite' }}></span>
                  Streaming
                </span>
              )}
            </div>

            <div ref={consoleRef} className="console-view">
              {logs.map((line, idx) => {
                let className = 'console-line';
                if (line.startsWith('[ERROR]') || line.startsWith('[STDERR]')) className += ' error';
                else if (line.startsWith('[SYSTEM]')) className += ' info';
                return (
                  <div key={idx} className={className}>
                    {line}
                  </div>
                );
              })}
              {logs.length === 0 && (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '120px' }}>
                  No execution logs active. Run the scraper to start log capture stream.
                </div>
              )}
            </div>
          </section>

          {/* Scraped Results Viewer */}
          <section className="glass-panel" style={{ padding: '24px', flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Database size={20} style={{ color: 'var(--primary)' }} />
                  {selectedRunId ? 'Historical Run Posts' : 'Database Scraped Posts'}
                </h2>
                {(selectedRunId ? historyLastUpdated : lastUpdated) && (
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {selectedRunId ? `Run time: ${historyLastUpdated}` : `Last run update: ${lastUpdated}`}
                  </span>
                )}
              </div>

              {/* Filter and Export Actions */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {/* Leads / Rejections filter */}
                <div style={{ display: 'flex', padding: '2px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                  <button 
                    onClick={() => setLeadFilter('all')}
                    style={{
                      border: 'none',
                      background: leadFilter === 'all' ? 'rgba(255,255,255,0.08)' : 'none',
                      color: leadFilter === 'all' ? 'var(--text-primary)' : 'var(--text-secondary)',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    All ({(historyLeads !== null ? historyLeads : leads).length + (historyNotLeads !== null ? historyNotLeads : notLeads).length})
                  </button>
                  <button 
                    onClick={() => setLeadFilter('leads')}
                    style={{
                      border: 'none',
                      background: leadFilter === 'leads' ? 'rgba(16, 185, 129, 0.15)' : 'none',
                      color: leadFilter === 'leads' ? 'var(--success)' : 'var(--text-secondary)',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    Leads ({(historyLeads !== null ? historyLeads : leads).length})
                  </button>
                  <button 
                    onClick={() => setLeadFilter('rejected')}
                    style={{
                      border: 'none',
                      background: leadFilter === 'rejected' ? 'rgba(239, 68, 68, 0.15)' : 'none',
                      color: leadFilter === 'rejected' ? 'var(--error)' : 'var(--text-secondary)',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    Rejected ({(historyNotLeads !== null ? historyNotLeads : notLeads).length})
                  </button>
                </div>

                {/* Export CSV button */}
                <button 
                  onClick={exportToCSV}
                  className="btn btn-secondary"
                  style={{
                    padding: '6px 12px',
                    fontSize: '12px',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: 'pointer',
                    height: '32px'
                  }}
                >
                  <Download size={14} />
                  Export CSV
                </button>
              </div>
            </div>

            {/* List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', maxHeight: '450px', flex: 1 }}>
              {filteredPosts().map((post, idx) => (
                <div 
                  key={idx} 
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                      <span style={{ 
                        fontSize: '11px', 
                        background: post.is_lead ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        color: post.is_lead ? 'var(--success)' : 'var(--error)',
                        padding: '4px 10px',
                        borderRadius: '20px',
                        fontWeight: 600
                      }}>
                        {post.is_lead ? `Lead (Score: ${post.score})` : `Rejected (Score: ${post.score})`}
                      </span>
                      {post.scraped_at && (
                        <span style={{ fontSize: '11px', color: 'var(--text-secondary)', background: 'rgba(255, 255, 255, 0.05)', padding: '4px 10px', borderRadius: '20px' }}>
                          ⏱️ ดึงเมื่อ: {post.scraped_at}
                        </span>
                      )}
                      {post.time && (
                        <span style={{ fontSize: '11px', color: 'var(--text-secondary)', background: 'rgba(255, 255, 255, 0.05)', padding: '4px 10px', borderRadius: '20px' }}>
                          🕒 โพสต์เมื่อ: {post.time}
                        </span>
                      )}
                    </div>
                    <a 
                      href={post.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      style={{ fontSize: '12px', color: 'var(--primary)', textDecoration: 'none', whiteSpace: 'nowrap' }}
                    >
                      View Facebook Post &rarr;
                    </a>
                  </div>

                  <p style={{ fontSize: '13px', lineHeight: 1.5, color: 'var(--text-primary)' }}>
                    {post.message}
                  </p>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-color)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <div>
                      <strong>AI Reason:</strong> <span style={{ color: 'var(--text-primary)' }}>{post.reason || 'No reasoning captured'}</span>
                    </div>
                    {post.contact && (
                      <span style={{ background: 'var(--bg-tag)', color: 'var(--text-tag)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px' }}>
                        {post.contact}
                      </span>
                    )}
                  </div>
                </div>
              ))}
              
              {filteredPosts().length === 0 && (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '40px' }}>
                  No posts recorded in database. Run scraper to gather and index new posts.
                </div>
              )}
            </div>

          </section>

        </div>

      </div>

    </div>
  );
}
