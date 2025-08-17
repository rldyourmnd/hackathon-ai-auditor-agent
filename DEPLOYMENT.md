# Deployment Setup

## GitHub Actions Auto-Deployment

This repository is configured with GitHub Actions to automatically deploy to your VPS when changes are pushed to the `main` branch.

### Required GitHub Secrets

Go to your GitHub repository settings → Secrets and variables → Actions, and add these secrets:

#### 1. VPS_SSH_KEY
Your private SSH key for connecting to the VPS:
```bash
# Generate SSH key pair on your local machine (if not exists)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy the PRIVATE key content (usually ~/.ssh/id_rsa)
cat ~/.ssh/id_rsa
```
Copy the entire private key content including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`

#### 2. VPS_USER
Your VPS username (e.g., `root`, `ubuntu`, `deploy`)

#### 3. VPS_HOST
Your VPS IP address or domain (e.g., `123.45.67.89` or `yourdomain.com`)

#### 4. VPS_PROJECT_PATH
Absolute path to your project on the VPS (e.g., `/home/user/hackathon-ai-auditor-agent`)

### VPS Setup

1. **Install required software on your VPS:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER

   # Install Docker Compose
   sudo apt install docker-compose-plugin

   # Install Git
   sudo apt install git
   ```

2. **Setup SSH access:**
   ```bash
   # Add your public key to VPS authorized_keys
   # Copy your public key content (usually ~/.ssh/id_rsa.pub)
   echo "YOUR_PUBLIC_KEY_CONTENT" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   ```

3. **Clone the repository on VPS:**
   ```bash
   git clone https://github.com/rldyourmnd/hackathon-ai-auditor-agent.git
   cd hackathon-ai-auditor-agent
   ```

4. **Setup environment variables:**
   ```bash
   # Copy and configure environment
   cp .env.example .env
   # Edit .env with your actual values
   nano .env
   ```

5. **Initial deployment:**
   ```bash
   cd infra
   docker compose up -d
   ```

### Workflow Triggers

The deployment workflow runs:
- **Automatically** when code is pushed to `main` branch
- **Manually** via GitHub Actions web interface

### Deployment Process

1. Connects to VPS via SSH
2. Pulls latest code from `main` branch
3. Stops existing Docker containers
4. Rebuilds containers with latest code
5. Starts all services
6. Runs health checks

### Monitoring

Check deployment status:
- GitHub Actions tab in your repository
- VPS logs: `docker compose logs -f`
- Service status: `docker compose ps`

### Troubleshooting

Common issues:
- **SSH connection failed**: Check VPS_SSH_KEY, VPS_USER, VPS_HOST secrets
- **Permission denied**: Ensure SSH key is added to VPS authorized_keys
- **Docker build failed**: Check VPS disk space and Docker daemon status
- **Services not starting**: Check .env file and port conflicts

### Security Notes

- Never commit SSH keys or secrets to the repository
- Use SSH key authentication, not passwords
- Keep your VPS system updated
- Configure firewall to restrict access to necessary ports only
