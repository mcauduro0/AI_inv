# Secrets Management Guide

This guide explains how to securely manage API keys and secrets for the Investment Agent System.

## Table of Contents

- [Overview](#overview)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Required API Keys](#required-api-keys)
- [Security Best Practices](#security-best-practices)

## Overview

The Investment Agent System requires various API keys and secrets to function. These include:

- **LLM Provider Keys**: OpenAI, Anthropic, Gemini, Perplexity
- **Financial Data Keys**: Polygon.io, FMP, Trading Economics, FRED
- **Infrastructure Keys**: DigitalOcean, Database passwords
- **Authentication Secrets**: JWT secrets, internal API keys

**IMPORTANT**: Never commit actual secrets to version control!

## Local Development

### Step 1: Create Local Environment File

```bash
# Copy the template
cp .env .env.local

# Edit with your actual keys
nano .env.local
```

### Step 2: Add Your API Keys

Edit `.env.local` and fill in your actual API keys:

```bash
# LLM Providers
OPENAI_API_KEY=sk-your-actual-openai-key
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key
GEMINI_API_KEY=your-actual-gemini-key
SONAR_API_KEY=pplx-your-actual-perplexity-key

# Financial Data
POLYGON_API_KEY=your-actual-polygon-key
FMP_API_KEY=your-actual-fmp-key
TRADING_ECONOMICS_CLIENT_KEY=your-actual-te-client-key
TRADING_ECONOMICS_SECRET_KEY=your-actual-te-secret-key
```

### Step 3: Use Local Environment

```bash
# Option 1: Source the file
source .env.local

# Option 2: Use docker-compose with env file
docker-compose --env-file .env.local up -d
```

### Step 4: Add to .gitignore

Ensure `.env.local` is in `.gitignore`:

```bash
echo ".env.local" >> .gitignore
```

## Production Deployment

### Option 1: Environment Variables (Recommended for Terraform)

Set environment variables before running Terraform:

```bash
# DigitalOcean Token
export TF_VAR_do_token="dop_v1_your-actual-token"

# Run Terraform
cd infra
terraform init
terraform plan -var-file="environments/prod/terraform.tfvars"
terraform apply -var-file="environments/prod/terraform.tfvars"
```

### Option 2: Kubernetes Secrets

Create secrets in Kubernetes:

```bash
# Create namespace
kubectl create namespace investment-agent-system

# Create secrets from literal values
kubectl create secret generic llm-api-keys \
    --namespace=investment-agent-system \
    --from-literal=openai-api-key="sk-your-key" \
    --from-literal=anthropic-api-key="sk-ant-your-key" \
    --from-literal=gemini-api-key="your-key" \
    --from-literal=perplexity-api-key="pplx-your-key"

kubectl create secret generic financial-api-keys \
    --namespace=investment-agent-system \
    --from-literal=polygon-api-key="your-key" \
    --from-literal=fmp-api-key="your-key" \
    --from-literal=trading-economics-client-key="your-key" \
    --from-literal=trading-economics-secret-key="your-key"

kubectl create secret generic auth-secrets \
    --namespace=investment-agent-system \
    --from-literal=jwt-secret="$(openssl rand -base64 32)" \
    --from-literal=internal-api-key="$(openssl rand -base64 32)"
```

### Option 3: DigitalOcean App Platform Secrets

If using DigitalOcean App Platform:

1. Go to your app in the DigitalOcean console
2. Navigate to Settings > App-Level Environment Variables
3. Add each secret as an encrypted environment variable

### Option 4: HashiCorp Vault (Enterprise)

For enterprise deployments, use HashiCorp Vault:

```bash
# Store secrets in Vault
vault kv put secret/investment-agent/llm \
    openai_api_key="sk-your-key" \
    anthropic_api_key="sk-ant-your-key"

# Configure Kubernetes to use Vault
# (requires Vault Agent Injector)
```

## Required API Keys

### LLM Providers

| Provider | Key Name | Where to Get |
|----------|----------|--------------|
| OpenAI | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| Anthropic | `ANTHROPIC_API_KEY` | https://console.anthropic.com/ |
| Google Gemini | `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey |
| Perplexity | `SONAR_API_KEY` | https://www.perplexity.ai/settings/api |
| ElevenLabs | `ELEVENLABS_API_KEY` | https://elevenlabs.io/ |

### Financial Data Providers

| Provider | Key Name | Where to Get |
|----------|----------|--------------|
| Polygon.io | `POLYGON_API_KEY` | https://polygon.io/ |
| FMP | `FMP_API_KEY` | https://financialmodelingprep.com/ |
| Trading Economics | `TRADING_ECONOMICS_CLIENT_KEY`, `TRADING_ECONOMICS_SECRET_KEY` | https://tradingeconomics.com/api |
| FRED | `FRED_API_KEY` | https://fred.stlouisfed.org/docs/api/api_key.html |

### Social/Alternative Data

| Provider | Key Name | Where to Get |
|----------|----------|--------------|
| Reddit | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | https://www.reddit.com/prefs/apps |
| Twitter/X | `TWITTER_BEARER_TOKEN` | https://developer.twitter.com/ |

### Infrastructure

| Provider | Key Name | Where to Get |
|----------|----------|--------------|
| DigitalOcean | `DIGITALOCEAN_TOKEN` | https://cloud.digitalocean.com/account/api/tokens |

## Security Best Practices

### 1. Never Commit Secrets

- Use `.gitignore` to exclude secret files
- Use git-secrets or similar tools to prevent accidental commits
- Review commits before pushing

### 2. Rotate Keys Regularly

- Rotate API keys every 90 days
- Immediately rotate if a key is compromised
- Use key rotation automation where available

### 3. Use Least Privilege

- Create API keys with minimal required permissions
- Use separate keys for development and production
- Revoke unused keys

### 4. Encrypt at Rest

- Use encrypted secret storage (Kubernetes Secrets, Vault)
- Enable encryption for databases and storage
- Use TLS for all communications

### 5. Audit Access

- Log all secret access
- Monitor for unusual API usage
- Set up alerts for suspicious activity

### 6. Secure CI/CD

- Use CI/CD secret management (GitHub Secrets, GitLab CI Variables)
- Never print secrets in logs
- Use ephemeral credentials where possible

## Quick Reference Commands

### Generate Secure Secrets

```bash
# Generate JWT secret
openssl rand -base64 32

# Generate API key
openssl rand -hex 32

# Generate password
openssl rand -base64 24
```

### Verify Secrets Are Not Committed

```bash
# Check for secrets in git history
git log -p | grep -i "api_key\|secret\|password\|token"

# Use git-secrets (install first)
git secrets --scan
```

### Encrypt Secrets File

```bash
# Using GPG
gpg --symmetric --cipher-algo AES256 .env.local

# Decrypt
gpg --decrypt .env.local.gpg > .env.local
```

## Troubleshooting

### "API key invalid" errors

1. Verify the key is correct (no extra spaces)
2. Check if the key has expired
3. Verify the key has required permissions

### Secrets not loading

1. Check file permissions: `chmod 600 .env.local`
2. Verify environment variables are exported
3. Check for typos in variable names

### Kubernetes secrets not working

1. Verify secret exists: `kubectl get secrets -n investment-agent-system`
2. Check secret is mounted correctly in pod
3. Verify service account has access to secret

---

For additional help, please open an issue on GitHub.
