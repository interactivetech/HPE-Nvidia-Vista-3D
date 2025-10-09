#!/bin/bash
# NVIDIA NGC Container Registry Login Helper
# This script logs you into NGC so you can pull Vista3D images

set -e

# Colors for output
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
CYAN='\033[96m'
BOLD='\033[1m'
END='\033[0m'

echo -e "\n${BOLD}${CYAN}=====================================================================${END}"
echo -e "${BOLD}${CYAN}           NVIDIA NGC Container Registry Login                       ${END}"
echo -e "${BOLD}${CYAN}=====================================================================${END}\n"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found in backend directory${END}"
    echo -e "${BLUE}ℹ️  Please run the setup script first: python3 setup.py${END}"
    exit 1
fi

# Load NGC_API_KEY from .env
source .env

# Check if NGC_API_KEY is set
if [ -z "$NGC_API_KEY" ] || [ "$NGC_API_KEY" == '""' ] || [ "$NGC_API_KEY" == "" ]; then
    echo -e "${YELLOW}⚠️  NGC_API_KEY is not set in .env file${END}"
    echo -e "${BLUE}ℹ️  You need an NVIDIA NGC API key to access Vista3D${END}"
    echo -e "${BLUE}ℹ️  Get your free API key at: https://ngc.nvidia.com/${END}"
    echo ""
    read -p "Enter your NGC API key (starts with 'nvapi-'): " API_KEY
    
    if [[ ! "$API_KEY" =~ ^nvapi- ]]; then
        echo -e "${RED}❌ Invalid API key format. Must start with 'nvapi-'${END}"
        exit 1
    fi
    
    # Update .env file with the new API key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|NGC_API_KEY=\".*\"|NGC_API_KEY=\"$API_KEY\"|g" .env
    else
        # Linux
        sed -i "s|NGC_API_KEY=\".*\"|NGC_API_KEY=\"$API_KEY\"|g" .env
    fi
    
    NGC_API_KEY="$API_KEY"
    echo -e "${GREEN}✅ Updated .env file with NGC_API_KEY${END}"
fi

# Remove quotes if present
NGC_API_KEY=$(echo "$NGC_API_KEY" | tr -d '"')

echo -e "${BLUE}ℹ️  Logging into nvcr.io...${END}"
echo ""

# Login to NGC
echo "$NGC_API_KEY" | docker login nvcr.io -u '$oauthtoken' --password-stdin

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Successfully logged into NVIDIA NGC Container Registry${END}"
    echo -e "${BLUE}ℹ️  You can now pull Vista3D images${END}"
    echo ""
    echo -e "${BOLD}${CYAN}=====================================================================${END}"
    echo -e "${BOLD}${CYAN}                    Next Steps                                       ${END}"
    echo -e "${BOLD}${CYAN}=====================================================================${END}\n"
    echo -e "${GREEN}To start the Vista3D backend:${END}"
    echo -e "  ${BOLD}docker compose up -d${END}"
    echo ""
    echo -e "${GREEN}To check status:${END}"
    echo -e "  ${BOLD}docker compose ps${END}"
    echo ""
    echo -e "${GREEN}To view logs:${END}"
    echo -e "  ${BOLD}docker compose logs -f${END}"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Failed to log into NGC${END}"
    echo -e "${BLUE}ℹ️  Please check your API key and try again${END}"
    exit 1
fi

