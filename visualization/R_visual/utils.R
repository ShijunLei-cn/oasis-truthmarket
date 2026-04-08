# Oasis Truth Market Visualization Package
# R version for paper figures
#
# Required packages: ggplot2, dplyr, tidyr, jsonlite, RSQLite, scico, ggsignif
# Install with: install.packages(c("ggplot2", "dplyr", "tidyr", "jsonlite", "RSQLite", "scico", "ggsignif"))

# ============================================================
# Color Palette (consistent with Python version)
# ============================================================

# Core Semantic Colors
COLORS <- list(
  # Good-outcome greens
  good_dark = "#1D6B3A",
  good_mid = "#52B788",
  good_light = "#C8E6C9",
  
  # Product quality
  hq_auth = "#2D6A4F",
  lq_auth = "#74C69D",
  
  # Bad-outcome reds
  bad_dark = "#AE2012",
  bad_mid = "#D4866A",
  bad_light = "#F4C9BA",
  counterfeit = "#9B2226",
  
  # Neutral grays
  neutral = "#6B6B6B",
  neutral_dark = "#2D2D2D",
  neutral_light = "#EEEEEE",
  
  # Accent
  accent = "#1A4E8A",
  
  # Communication & Mechanism
  comm_dark = "#1565c0",
  comm_mid = "#64b5f6",
  comm_baseline = "#90caf9",
  
  rep_dark = "#1a7a3a",
  rep_mid = "#4caf72",
  warrant_dark = "#1565c0",
  warrant_mid = "#64b5f6"
)

# Condition colors for line charts (RQ3)
CONDITION_COLORS <- c(
  "Rep" = "#AAAAAA",
  "Rep, Comm" = "#52B788",
  "Rep+Warrant" = "#2B6CB0",
  "Rep+Warrant, Comm" = "#1A4E8A"
)

# ============================================================
# Theme Setup
# ============================================================

setup_theme <- function() {
  theme_bw() %+replace%
    theme(
      # Typography
      text = element_text(family = "sans-serif", size = 9),
      axis.text = element_text(size = 8),
      axis.title = element_text(size = 9),
      plot.title = element_text(size = 10, face = "bold"),
      
      # Spines
      axis.line = element_line(linewidth = 0.7),
      panel.border = element_blank(),
      
      # Grid
      panel.grid = element_blank(),
      axis.ticks = element_line(linewidth = 0.7),
      
      # Legend
      legend.position = "top",
      legend.text = element_text(size = 8),
      legend.title = element_text(size = 9, face = "bold")
    )
}

# ============================================================
# Data Loading Functions
# ============================================================

#' Load results from experiment directory
#' @param experiment_dir Path to experiment directory
#' @return DataFrame with results
load_results_df <- function(experiment_dir) {
  results_files <- list.files(experiment_dir, pattern = "run_.*_results\\.json", full.names = TRUE)
  
  if (length(results_files) == 0) {
    warning(paste("No results files found in", experiment_dir))
    return(data.frame())
  }
  
  all_results <- lapply(results_files, function(f) {
    json_data <- jsonlite::fromJSON(f)
    run_id <- as.integer(gsub(".*run_(\\d+)_results.*", "\\1", f))
    json_data$run_id <- run_id
    json_data
  })
  
  do.call(rbind, all_results)
}

#' Load cognitive probes from experiment directory
#' @param experiment_dir Path to experiment directory
#' @return DataFrame with probe results
load_probes_df <- function(experiment_dir) {
  probe_files <- list.files(experiment_dir, pattern = "run_.*_cognitive_probes\\.json", full.names = TRUE)
  
  if (length(probe_files) == 0) {
    return(data.frame())
  }
  
  all_probes <- lapply(probe_files, function(f) {
    json_data <- jsonlite::fromJSON(f)
    run_id <- as.integer(gsub(".*run_(\\d+)_cognitive_probes.*", "\\1", f))
    json_data$run_id <- run_id
    json_data
  })
  
  do.call(rbind, all_probes)
}

#' Load data from SQLite database
#' @param db_path Path to SQLite database
#' @param query SQL query string
#' @return DataFrame with query results
query_db <- function(db_path, query) {
  con <- dbConnect(RSQLite::SQLite(), db_path)
  on.exit(dbDisconnect(con))
  dbGetQuery(con, query)
}

# ============================================================
# Aggregation Functions
# ============================================================

#' Count deceptions per run
#' @param df Results dataframe
#' @return Vector of deception counts per run
count_deceptions <- function(df) {
  aggregate(is_honest ~ run_id, data = df, 
            FUN = function(x) sum(!x, na.rm = TRUE))$is_honest
}

#' Sum seller profit per run
#' @param df Results dataframe
#' @return Vector of total profit per run
sum_seller_profit <- function(df) {
  aggregate(seller_profit ~ run_id, data = df, 
            FUN = sum, na.rm = TRUE)$seller_profit
}

#' Sum buyer utility per run
#' @param df Results dataframe
#' @return Vector of total utility per run
sum_buyer_utility <- function(df) {
  aggregate(buyer_utility ~ run_id, data = df, 
            FUN = sum, na.rm = TRUE)$buyer_utility
}

#' Count product quality (hq_auth, lq_auth, hq_counterfeit)
#' @param df Results dataframe
#' @return DataFrame with counts per run
product_quality_counts <- function(df) {
  # Determine column names
  q_col <- grep("quality|actual_quality|true_quality", names(df), value = TRUE)[1]
  a_col <- "advertised_quality"
  s_col <- grep("sold|is_sold", names(df), value = TRUE)[1]
  
  if (is.na(q_col) || is.na(a_col)) {
    return(data.frame(run_id = integer(), hq_auth = numeric(), lq_auth = numeric(), hq_cfeit = numeric()))
  }
  
  # Convert to uppercase for comparison
  df[[q_col]] <- toupper(df[[q_col]])
  df[[a_col]] <- toupper(df[[a_col]])
  
  # Filter sold products if column exists
  if (!is.na(s_col)) {
    df <- df[df[[s_col]] == TRUE, ]
  }
  
  # Count categories
  hq_auth <- sum(df[[a_col]] == "HQ" & df[[q_col]] == "HQ", na.rm = TRUE)
  lq_auth <- sum(df[[a_col]] == "LQ" & df[[q_col]] == "LQ", na.rm = TRUE)
  hq_cfeit <- sum(df[[a_col]] == "HQ" & df[[q_col]] == "LQ", na.rm = TRUE)
  
  data.frame(
    run_id = unique(df$run_id),
    hq_auth = hq_auth,
    lq_auth = lq_auth,
    hq_cfeit = hq_cfeit
  )
}

# ============================================================
# Statistical Tests
# ============================================================

#' Mann-Whitney U test
#' @param a,b Numeric vectors
#' @return p-value
mannwhitney_p <- function(a, b) {
  a <- a[!is.na(a)]
  b <- b[!is.na(b)]
  
  if (length(a) < 2 || length(b) < 2) {
    return(1.0)
  }
  
  tryCatch(
    wilcox.test(a, b, alternative = "two-sided")$p.value,
    error = function(e) 1.0
  )
}

#' Significance marker display
#' @param p p-value
#' @return String with significance markers or NA
sig_marker <- function(p) {
  if (p < 0.001) return("***")
  if (p < 0.01) return("**")
  if (p < 0.05) return("*")
  return(NA)
}

# ============================================================
# Plotting Helper Functions
# ============================================================

#' Add significance bracket
#' @param p Plot object
#' @param x1,x2 X positions
#' @param y Y position
#' @param p_val p-value
add_significance_bracket <- function(p, x1, x2, y, p_val) {
  marker <- sig_marker(p_val)
  if (is.na(marker)) return(p)
  
  # Simple bracket line
  p + annotate("segment", x = x1, xend = x1, y = y * 0.95, yend = y * 0.98) +
    annotate("segment", x = x2, xend = x2, y = y * 0.95, yend = y * 0.98) +
    annotate("segment", x = x1, xend = x2, y = y, yend = y) +
    annotate("text", x = (x1 + x2) / 2, y = y * 1.02, label = marker, vjust = 0)
}

# ============================================================
# Export Functions
# ============================================================

#' Save figure to file
#' @param p Plot object
#' @param filename Output filename
#' @param width Width in inches
#' @param height Height in inches
save_figure <- function(p, filename, width = 8, height = 6) {
  dir.create(dirname(filename), recursive = TRUE, showWarnings = FALSE)
  ggsave(filename, p, width = width, height = height, dpi = 300)
  message(paste("Saved:", filename))
}
