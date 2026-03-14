---
name: twikit-cli
description: "Twitter/X data retrieval using the twikit-cli command-line tool. Use when users need to: (1) Search tweets or users on Twitter/X, (2) Get user profiles, timelines, followers, (3) View trending topics and hashtags, (4) Retrieve specific tweet details, (5) Authenticate with Twitter/X, or any other Twitter/X data collection tasks. Works without official API keys."
---

# twikit-cli

Help users construct correct twikit-cli commands for Twitter/X data retrieval.

## Quick Start

twikit-cli is a Twitter/X information retrieval tool built on twikit. It requires authentication before use:

```bash
# First time: authenticate
twikit-cli auth login

# Then use any command
twikit-cli search tweets "keyword"
twikit-cli user info @username
twikit-cli trends
```

## Core Operations

### Authentication
```bash
twikit-cli auth login                      # Interactive login
twikit-cli auth set-cookies cookies.json   # Import browser cookies
```

### Search
```bash
twikit-cli search tweets "query" [--type Latest|Top|Media] [--count N]
twikit-cli search users "query" [--count N]
```

### User Operations
```bash
twikit-cli user info @username
twikit-cli user tweets @username [--type Tweets|Replies|Media|Likes] [--count N]
twikit-cli user followers @username [--count N]
```

### Trends and Tweets
```bash
twikit-cli trends [--category trending|for-you|news|sports|entertainment] [--count N]
twikit-cli tweet get <tweet_id>
```

## Global Options

All commands support these global options (before the subcommand):

```bash
twikit-cli [--proxy URL] [--cookies FILE] [--lang CODE] [--json-output] <command>
```

- `--proxy`: HTTP proxy (or use `TWIKIT_PROXY` env var)
- `--cookies`: Custom cookies file path
- `--lang`: Language code (default: en-US)
- `--json-output`: Output raw JSON for piping

## Complete Reference

For detailed command syntax, options, and examples, read [cli_usage.md](references/cli_usage.md).

## When Helping Users

1. Ask clarifying questions if the task is ambiguous
2. Reference cli_usage.md for specific syntax and options when needed
3. Construct complete commands with appropriate options
4. Remind users about authentication if they haven't set it up
5. Suggest `--json-output` when users want to process data programmatically
6. Recommend proxy configuration for users in restricted regions
