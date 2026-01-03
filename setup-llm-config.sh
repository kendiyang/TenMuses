#!/bin/bash
# Setup LLM configurations in database

set -e

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/backend" && pwd)"
VENV_PYTHON="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.venv/bin/python"

echo "================================"
echo "TenMuses LLM Configuration Setup"
echo "================================"
echo ""

# Check if Python virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Python virtual environment not found at $VENV_PYTHON"
    echo ""
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

echo "✓ Python environment found"
echo ""

# Prompt for OpenAI API Key
echo "Enter OpenAI API Key (or press Enter to skip):"
read -s OPENAI_API_KEY

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Skipping OpenAI configuration"
else
    echo "✓ OpenAI API Key provided"
fi

echo ""

# Prompt for Anthropic API Key
echo "Enter Anthropic API Key (or press Enter to skip):"
read -s ANTHROPIC_API_KEY

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Skipping Anthropic configuration"
else
    echo "✓ Anthropic API Key provided"
fi

echo ""

# Create a temporary Python script to save configurations
cat > /tmp/setup_llm_config.py << 'EOF'
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import AsyncSessionLocal
from app.services.config_service import ConfigService

async def setup():
    openai_key = os.environ.get('OPENAI_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    
    async with AsyncSessionLocal() as session:
        if openai_key:
            print("Setting up OpenAI configuration...")
            config = await ConfigService.save_provider_config(
                session,
                provider="openai",
                model_name="gpt-4-turbo-preview",
                api_key=openai_key,
                base_url=None,
                display_name="OpenAI GPT-4 Turbo",
                description="OpenAI's GPT-4 Turbo model",
                priority=10,
            )
            await session.commit()
            print(f"✓ OpenAI configuration saved")
        
        if anthropic_key:
            print("Setting up Anthropic configuration...")
            config = await ConfigService.save_provider_config(
                session,
                provider="anthropic",
                model_name="claude-3-sonnet-20240229",
                api_key=anthropic_key,
                base_url=None,
                display_name="Anthropic Claude 3 Sonnet",
                description="Anthropic's Claude 3 Sonnet model",
                priority=20,
            )
            await session.commit()
            print(f"✓ Anthropic configuration saved")
        
        if not openai_key and not anthropic_key:
            print("No API keys provided")
            return 1
        
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(setup())
    sys.exit(exit_code)
EOF

# Set environment variables and run the setup script
export OPENAI_API_KEY="$OPENAI_API_KEY"
export ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"

echo "Saving configuration to database..."
if $VENV_PYTHON /tmp/setup_llm_config.py; then
    echo ""
    echo "✓ Configuration saved successfully!"
    echo ""
    echo "You can now use the following API endpoints:"
    echo "  - GET  /api/v1/config/llm/providers       - List all LLM providers"
    echo "  - GET  /api/v1/config/llm/providers/openai       - Get OpenAI config"
    echo "  - GET  /api/v1/config/llm/providers/anthropic    - Get Anthropic config"
    echo "  - POST /api/v1/config/llm/providers       - Create/update provider config"
    echo "  - PATCH /api/v1/config/llm/providers/{provider}/toggle - Toggle provider"
else
    echo ""
    echo "❌ Failed to save configuration"
    exit 1
fi

rm -f /tmp/setup_llm_config.py
