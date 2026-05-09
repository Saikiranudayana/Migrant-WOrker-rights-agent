# How to Get Your API Keys

This guide walks you through getting every API key required for ShramMitra AI.
After you have each value, paste it into `.env` (the file in your project root).

---

## Table of Contents

1. [Elastic Cloud — Elasticsearch & Jina Embeddings](#1-elastic-cloud)
2. [AWS — Bedrock, EC2, S3, Transcribe, Polly](#2-aws)
3. [WhatsApp Business Cloud API](#3-whatsapp)
4. [Quick Checklist](#4-checklist)

---

## 1. Elastic Cloud

### 1.1 Create a Deployment

1. Go to **[cloud.elastic.co](https://cloud.elastic.co)** and sign in (or create a free trial account).
2. Click **Create deployment**.
3. Choose:
   - **Cloud provider**: AWS
   - **Region**: `ap-south-1` (Mumbai) — closest to Bengaluru users
   - **Hardware profile**: Storage optimized (for vector search)
   - **Version**: 9.x (latest)
4. Give the deployment a name — e.g., `shrammitra-prod`.
5. Click **Create deployment**. Wait ~3 minutes for it to provision.
6. **Save the `elastic` superuser password** shown on the confirmation screen — you cannot retrieve it later.

---

### 1.2 Get the Elasticsearch Endpoint URL

1. In your deployment, click **Manage** → **Copy endpoint**.
2. It looks like:
   ```
   https://abc123def456.ap-south-1.aws.elastic.cloud:9243
   ```
3. Paste this into `.env`:
   ```
   ELASTICSEARCH_URL=https://abc123def456.ap-south-1.aws.elastic.cloud:9243
   ```

---

### 1.3 Create an API Key

> API keys are safer than using the `elastic` password directly.

1. In your deployment, click **Open Kibana**.
2. In Kibana, go to **Stack Management** → **API Keys** (under Security).
3. Click **Create API key**.
4. Set:
   - **Name**: `shrammitra-backend`
   - **Expiry**: No expiration (or set a rotation schedule)
   - **Privileges**: Leave as **Restrict privileges** and add:
     ```json
     {
       "shrammitra_backend": {
         "indices": [
           {
             "names": ["shrammitra_labour_docs*"],
             "privileges": ["read", "write", "create_index", "manage"]
           }
         ],
         "cluster": ["manage_inference"]
       }
     }
     ```
5. Click **Create API key**.
6. Copy the **Base64 encoded** value shown (it looks like `dV8t...Zw==`).
7. Paste into `.env`:
   ```
   ELASTICSEARCH_API_KEY=dV8t...Zw==
   ```
   > Do **not** wrap it in quotes in the `.env` file.

---

### 1.4 Set Up Jina v5 Inference Endpoint

> This lets Elasticsearch call Jina AI to generate embeddings — data stays in Elastic.

**Get your Jina API key:**
1. Go to **[jina.ai](https://jina.ai)** → Sign up / Sign in.
2. Click your avatar → **API Keys**.
3. Click **Create new key** → copy the key (`jina_...`).
4. Paste into `.env`:
   ```
   JINA_API_KEY=jina_xxxxxxxxxxxxxxxxxxxxxxxx
   ```

**Create the Elastic Inference Endpoint** (run once after Elasticsearch is up):
```bash
curl -X PUT "https://YOUR_CLUSTER_URL/_inference/text_embedding/jina-embeddings-v3" \
  -H "Authorization: ApiKey YOUR_ELASTICSEARCH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "jinaai",
    "service_settings": {
      "api_key": "YOUR_JINA_API_KEY",
      "model_id": "jina-embeddings-v3",
      "dimensions": 1024
    }
  }'
```

Or use the Makefile shortcut after Docker is running:
```bash
make create-index
```

---

## 2. AWS

### 2.1 Create an IAM User (for local dev)

> For production on EC2, use an IAM Role instead — skip to [2.4](#24-ec2-iam-role-production).

1. Sign in to **[console.aws.amazon.com](https://console.aws.amazon.com)**.
2. Search for **IAM** → **Users** → **Create user**.
3. Username: `shrammitra-local-dev`.
4. Select **Attach policies directly** and attach:
   - `AmazonBedrockFullAccess`
   - `AmazonTranscribeFullAccess`
   - `AmazonPollyFullAccess`
   - `AmazonS3FullAccess` *(scope to your bucket in production)*
5. Click **Create user**.
6. Click the user → **Security credentials** tab → **Create access key**.
7. Select **Application running outside AWS** → Next → Create.
8. Copy **Access key ID** and **Secret access key**.
9. Paste into `.env`:
   ```
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

### 2.2 Enable Amazon Bedrock — Claude 3 Sonnet

> Bedrock models are **not** enabled by default. You must request access.

1. In the AWS Console, switch region to **us-east-1** (N. Virginia).
2. Search for **Amazon Bedrock** → open it.
3. In the left sidebar click **Model access**.
4. Click **Manage model access** (top right).
5. Find **Anthropic → Claude 3 Sonnet** and tick the checkbox.
6. Click **Request model access** → Submit.
7. Approval is **usually instant** for Claude 3 Sonnet. Refresh the page after 1–2 minutes.
8. Confirm the status shows **Access granted**.

Your `.env` already has the correct model ID:
```
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

---

### 2.3 Create an S3 Bucket (for audio files)

1. In the AWS Console go to **S3** → **Create bucket**.
2. Settings:
   - **Bucket name**: `shrammitra-audio-dev-YOUR_NAME` (must be globally unique)
   - **Region**: `ap-south-1`
   - **Block all public access**: ✅ ON
   - **Server-side encryption**: AES-256
3. Click **Create bucket**.
4. Paste the bucket name into `.env`:
   ```
   S3_BUCKET_AUDIO=shrammitra-audio-dev-yourname
   TRANSCRIBE_OUTPUT_BUCKET=shrammitra-audio-dev-yourname
   ```

---

### 2.4 EC2 IAM Role (Production)

> On EC2, never put `AWS_ACCESS_KEY_ID` in `.env`. Use an IAM Role instead.

1. In IAM → **Roles** → **Create role**.
2. Trusted entity: **AWS service** → **EC2**.
3. Attach permissions:
   - `AmazonBedrockFullAccess`
   - `AmazonTranscribeFullAccess`
   - `AmazonPollyFullAccess`
   - Custom inline policy for your S3 bucket and Secrets Manager
4. Name it `shrammitra-ec2-role` → Create.
5. On your EC2 instance: **Actions** → **Security** → **Modify IAM role** → select `shrammitra-ec2-role`.
6. In `.env` on the EC2 instance, **leave these blank**:
   ```
   AWS_ACCESS_KEY_ID=
   AWS_SECRET_ACCESS_KEY=
   ```
   The AWS SDK will automatically use the instance profile.

---

### 2.5 Launch an EC2 Instance (Production)

1. In the AWS Console go to **EC2** → **Launch instance**.
2. Recommended settings:
   | Setting | Value |
   |---|---|
   | AMI | Amazon Linux 2023 |
   | Instance type | `t3.medium` (2 vCPU, 4 GB RAM) minimum |
   | Key pair | Create a new key pair, download `.pem` |
   | Security group | Allow port 22 (SSH), 80 (HTTP), 443 (HTTPS) |
   | Storage | 30 GB gp3 |
3. Attach the IAM role you created in step 2.4.
4. Click **Launch instance**.
5. SSH in:
   ```bash
   chmod 400 your-key.pem
   ssh -i your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
   ```
6. Install Docker on the instance:
   ```bash
   sudo yum update -y
   sudo yum install -y docker
   sudo service docker start
   sudo usermod -aG docker ec2-user
   # Log out and back in, then:
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

---

## 3. WhatsApp

> WhatsApp Business Cloud API is free for development. You need a Meta Developer account.

1. Go to **[developers.facebook.com](https://developers.facebook.com)** → **My Apps** → **Create App**.
2. App type: **Business**.
3. Add the **WhatsApp** product to your app.
4. In **WhatsApp → API Setup**:
   - Note your **Phone Number ID** → paste as `WHATSAPP_PHONE_NUMBER_ID`
   - Note your **WhatsApp Business Account ID** → paste as `WHATSAPP_BUSINESS_ACCOUNT_ID`
5. **Temporary access token** (good for 24h during dev):
   - Click **Generate access token** on the API Setup page.
   - For production, create a **System User token** under Business Settings.
   - Paste as `WHATSAPP_ACCESS_TOKEN`.
6. **App Secret**:
   - Go to **App Settings → Basic**.
   - Click **Show** next to App Secret.
   - Paste as `WHATSAPP_APP_SECRET`.
7. **Verify token**: choose any random string — e.g., `my-shrammitra-webhook-2024`.
   - Paste as `WHATSAPP_VERIFY_TOKEN`.
8. **Configure webhook** (after your server is running):
   - In **WhatsApp → Configuration**, set Callback URL to:
     ```
     https://YOUR_DOMAIN/webhook/whatsapp
     ```
   - Set Verify token to what you chose above.
   - Subscribe to field: **messages**.

---

## 4. Checklist

Copy this checklist and tick off each item before starting Docker:

```
ELASTIC CLOUD
[ ] ELASTICSEARCH_URL          — from Elastic Cloud deployment page
[ ] ELASTICSEARCH_API_KEY      — created in Kibana API Keys section
[ ] JINA_API_KEY               — from jina.ai account page

AWS
[ ] AWS_ACCESS_KEY_ID          — from IAM user security credentials
[ ] AWS_SECRET_ACCESS_KEY      — same
[ ] Bedrock Claude 3 Sonnet    — access granted in us-east-1
[ ] S3_BUCKET_AUDIO            — bucket created in ap-south-1

APPLICATION
[ ] SECRET_KEY                 — run: openssl rand -hex 32
[ ] ADMIN_API_KEY              — any strong password

WHATSAPP (can leave as placeholder for testing without WhatsApp)
[ ] WHATSAPP_PHONE_NUMBER_ID
[ ] WHATSAPP_ACCESS_TOKEN
[ ] WHATSAPP_APP_SECRET
[ ] WHATSAPP_VERIFY_TOKEN
```

> **Tip:** For local testing without WhatsApp, leave all `WHATSAPP_*` values as placeholders. The backend will start fine; only the `/webhook/whatsapp` endpoint will be non-functional.
