# Context Glossary - Facebook Bot Admin Dashboard

## Core Terms

### Unified Dashboard
A single web application interface that allows an administrator to manage multiple scraper projects (currently **HighSolar** and **C1**) from a single host and port. It provides switching capability between projects without needing separate application instances.

### HighSolar
The project configuration and scraper/poster system dedicated to collecting and filtering leads for the solar cell installation business.

### C1
The project configuration and scraper/poster system dedicated to collecting and filtering leads for the online computer rental business.

### Bot Run Status
The active or inactive state of the continuous loop scraper background process (`run_infi.py`).
- **Active / Running**: The script is running in the background, performing scraping and filtering loops every few minutes.
- **Inactive / Stopped**: The background process is not running.

### Real-time Log Streamer
A feature of the Unified Dashboard that displays the latest console output (stdout/stderr) of the scraper background process in near real-time, allowing administrators to monitor activity (e.g. current loop round, scraping status, errors) directly from the web browser.

