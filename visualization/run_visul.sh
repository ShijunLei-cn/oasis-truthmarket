#!/bin/bash
# Visualization script for market simulation results
# Provides convenient commands for generating visualizations from simulation data

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Function to print usage
usage() {
    echo "Usage: $0 <command> [arguments]"
    echo ""
    echo "Commands:"
    echo "  single <db_path> [--out <output_dir>]"
    echo "      Analyze a single simulation run"
    echo "      Example: $0 single experiments/exp_123/run_1.db"
    echo ""
    echo "  multi <experiment_id>"
    echo "      Analyze multi-run experiment results"
    echo "      Example: $0 multi exp_20251216_120000"
    echo ""
    echo "  compare <exp1_name>:<exp1_id> <exp2_name>:<exp2_id> [--out <output_dir>]"
    echo "      Compare two or more experiments"
    echo "      Example: $0 compare rep_only:exp_123 rep_warrant:exp_456"
    echo ""
    echo "  compare-config <config_file> [--out <output_dir>]"
    echo "      Compare experiments using a JSON config file"
    echo "      Example: $0 compare-config comparison_config.json"
    echo ""
    echo "Options:"
    echo "  --out <output_dir>    Specify output directory (optional)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Analyze single run"
    echo "  $0 single experiments/exp_20251216_120000/run_1.db"
    echo ""
    echo "  # Analyze multi-run experiment"
    echo "  $0 multi exp_20251216_120000"
    echo ""
    echo "  # Compare two experiments"
    echo "  $0 compare reputation_only:exp_20251216_120000 reputation_warrant:exp_20251216_130000"
    echo ""
    echo "  # Compare using config file"
    echo "  $0 compare-config comparison_config.json"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed or not in PATH${NC}" >&2
    exit 1
fi

# Check arguments
if [ $# -eq 0 ]; then
    usage
    exit 1
fi

# Parse command
COMMAND=$1
shift

case "$COMMAND" in
    single)
        if [ $# -eq 0 ]; then
            echo -e "${RED}Error: Database path required${NC}" >&2
            echo "Usage: $0 single <db_path> [--out <output_dir>]"
            exit 1
        fi
        
        DB_PATH=$1
        shift
        
        # Check if database exists
        if [ ! -f "$DB_PATH" ]; then
            echo -e "${RED}Error: Database file not found: $DB_PATH${NC}" >&2
            exit 1
        fi
        
        # Parse remaining arguments
        OUTPUT_DIR=""
        while [[ $# -gt 0 ]]; do
            case $1 in
                --out|--output)
                    OUTPUT_DIR="$2"
                    shift 2
                    ;;
                *)
                    echo -e "${RED}Error: Unknown option: $1${NC}" >&2
                    exit 1
                    ;;
            esac
        done
        
        echo -e "${GREEN}Analyzing single run: $DB_PATH${NC}"
        cd "$PROJECT_ROOT"
        
        if [ -z "$OUTPUT_DIR" ]; then
            python3 "$SCRIPT_DIR/analyze_single.py" "$DB_PATH"
        else
            python3 "$SCRIPT_DIR/analyze_single.py" "$DB_PATH" --out "$OUTPUT_DIR"
        fi
        ;;
    
    multi)
        if [ $# -eq 0 ]; then
            echo -e "${RED}Error: Experiment ID required${NC}" >&2
            echo "Usage: $0 multi <experiment_id>"
            exit 1
        fi
        
        EXPERIMENT_ID=$1
        shift
        
        echo -e "${GREEN}Analyzing multi-run experiment: $EXPERIMENT_ID${NC}"
        cd "$PROJECT_ROOT"
        python3 "$SCRIPT_DIR/analyze_multi.py" --experiment-id "$EXPERIMENT_ID"
        ;;
    
    compare)
        if [ $# -lt 2 ]; then
            echo -e "${RED}Error: Need at least 2 experiments to compare${NC}" >&2
            echo "Usage: $0 compare <exp1_name>:<exp1_id> <exp2_name>:<exp2_id> [--out <output_dir>]"
            exit 1
        fi
        
        # Parse experiments
        EXPERIMENTS=()
        OUTPUT_DIR=""
        
        while [[ $# -gt 0 ]]; do
            case $1 in
                --out|--output)
                    OUTPUT_DIR="$2"
                    shift 2
                    ;;
                -*)
                    echo -e "${RED}Error: Unknown option: $1${NC}" >&2
                    exit 1
                    ;;
                *)
                    if [[ "$1" == *":"* ]]; then
                        EXPERIMENTS+=("--exp" "$1")
                    else
                        echo -e "${RED}Error: Invalid format: $1 (expected name:id)${NC}" >&2
                        exit 1
                    fi
                    shift
                    ;;
            esac
        done
        
        if [ ${#EXPERIMENTS[@]} -lt 4 ]; then
            echo -e "${RED}Error: Need at least 2 experiments to compare${NC}" >&2
            exit 1
        fi
        
        echo -e "${GREEN}Comparing experiments...${NC}"
        cd "$PROJECT_ROOT"
        
        if [ -z "$OUTPUT_DIR" ]; then
            python3 "$SCRIPT_DIR/compare_experiments.py" "${EXPERIMENTS[@]}"
        else
            python3 "$SCRIPT_DIR/compare_experiments.py" "${EXPERIMENTS[@]}" --out "$OUTPUT_DIR"
        fi
        ;;
    
    compare-config)
        if [ $# -eq 0 ]; then
            echo -e "${RED}Error: Config file required${NC}" >&2
            echo "Usage: $0 compare-config <config_file> [--out <output_dir>]"
            exit 1
        fi
        
        CONFIG_FILE=$1
        shift
        
        # Check if config file exists
        if [ ! -f "$CONFIG_FILE" ]; then
            echo -e "${RED}Error: Config file not found: $CONFIG_FILE${NC}" >&2
            exit 1
        fi
        
        # Parse remaining arguments
        OUTPUT_DIR=""
        while [[ $# -gt 0 ]]; do
            case $1 in
                --out|--output)
                    OUTPUT_DIR="$2"
                    shift 2
                    ;;
                *)
                    echo -e "${RED}Error: Unknown option: $1${NC}" >&2
                    exit 1
                    ;;
            esac
        done
        
        echo -e "${GREEN}Comparing experiments using config: $CONFIG_FILE${NC}"
        cd "$PROJECT_ROOT"
        
        if [ -z "$OUTPUT_DIR" ]; then
            python3 "$SCRIPT_DIR/compare_experiments.py" --config-file "$CONFIG_FILE"
        else
            python3 "$SCRIPT_DIR/compare_experiments.py" --config-file "$CONFIG_FILE" --out "$OUTPUT_DIR"
        fi
        ;;
    
    -h|--help|help)
        usage
        ;;
    
    *)
        echo -e "${RED}Error: Unknown command: $COMMAND${NC}" >&2
        echo ""
        usage
        exit 1
        ;;
esac

exit $?
