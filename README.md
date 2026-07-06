# Gemini Workflow Test

This repository contains an automated workflow script (`gemini_workflow.py`) that tests the Gemini 1.5 Pro (or later) model's ability to implement GitHub issues autonomously.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory with the following variables:
```env
GITHUB_TOKEN=your_github_personal_access_token
GEMINI_API_KEY=your_gemini_api_key
GITHUB_REPO=username/repository
ISSUE_NUMBER=123
GEMINI_MODEL=gemini-1.5-pro # Optional, defaults to gemini-1.5-pro
```

## Usage

Run the script directly. It will fetch the issue, analyze the codebase, generate changes, apply them locally, push a new branch, and open a Pull Request.

```bash
python gemini_workflow.py
```
