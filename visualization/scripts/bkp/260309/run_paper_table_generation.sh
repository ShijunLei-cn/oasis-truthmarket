#!/bin/bash
# Paper Table Generation Script
# This script demonstrates how to generate all paper tables

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}Paper Table Generation${NC}"
echo -e "${BLUE}=======================================${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Warning: python3 not found. Trying 'python' instead.${NC}"
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Function to check if directory exists
check_dir() {
    if [ ! -d "$1" ]; then
        echo -e "${YELLOW}Warning: Directory $1 does not exist${NC}"
        return 1
    fi
    return 0
}

# Example usage (update paths to match your data)
echo -e "\n${GREEN}Example usage:${NC}"
echo "python generate_all_paper_tables.py \\"
echo "    --rq1 \\"
echo "        /path/to/rep_market_results \\"
echo "        /path/to/rep_probe_results \\"
echo "        /path/to/rep_warrant_market_results \\"
echo "        /path/to/rep_warrant_probe_results \\"
echo "    --rq2 \\"
echo "        /path/to/policy_making_exp \\"
echo "        /path/to/pressure_quick_profits_exp \\"
echo "        /path/to/psychological_attack_exp \\"
echo "    --rq3 \\"
echo "        /path/to/rep_comm_results \\"
echo "        /path/to/rep_warrant_comm_results \\"
echo "    --output-dir visualization/table/paper"

# Generate individual RQ tables
echo -e "\n${BLUE}Individual RQ generation:${NC}"
echo -e "${GREEN}RQ1:${NC} python generate_rq1_paper_tables.py --r-market-dir ... --r-probe-dir ... --rw-market-dir ... --rw-probe-dir ... --output-dir ..."
echo -e "${GREEN}RQ2:${NC} python generate_rq2_paper_tables.py --experiment-dirs dir1 dir2 dir3 --output-dir ..."
echo -e "${GREEN}RQ3:${NC} python generate_rq3_paper_tables.py --rep-comm-dir ... --rw-comm-dir ... --output-dir ..."

# Check dependencies
echo -e "\n${BLUE}Checking dependencies...${NC}"
$PYTHON_CMD -c "import pandas, numpy" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies OK${NC}"
else
    echo -e "${YELLOW}⚠ Some dependencies may be missing. Install with: pip install pandas numpy${NC}"
fi

# Create output directory if it doesn't exist
echo -e "\n${BLUE}Creating output directory...${NC}"
mkdir -p visualization/table/paper/rq1
mkdir -p visualization/table/paper/rq2
mkdir -p visualization/table/paper/rq3
echo -e "${GREEN}✓ Output directories created${NC}"

# List generated files
echo -e "\n${BLUE}Generated files will be:${NC}"
echo "  visualization/table/paper/rq1/"
echo "    - rq1_summary_stats.tex"
echo "    - rq1_summary_comparison.tex"
echo "    - rq1_product_quality.tex"
echo "  visualization/table/paper/rq2/"
echo "    - rq2_initial_posts.tex"
echo "    - rq2_product_quality.tex"
echo "    - rq2_profit_decomposition.tex"
echo "  visualization/table/paper/rq3/"
echo "    - rq3_summary_stats.tex"
echo "    - rq3_product_quality.tex"

echo -e "\n${GREEN}Ready to generate tables!${NC}"
echo -e "Update the paths in this script or use the commands above with your actual data directories."
