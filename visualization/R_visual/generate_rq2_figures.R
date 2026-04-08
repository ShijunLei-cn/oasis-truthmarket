#!/usr/bin/env Rscript
# ============================================================
# RQ2 Figures — Seller Communication under Constraints
# 
# Generates:
# - rq2_seller_comm_deception_by_constraint.png
# - rq2_profit_decomposition_honest_vs_dishonest.png
# - rq2_product_mix_appendix.png
# ============================================================

library(ggplot2)
library(dplyr)
library(tidyr)

source("visualization/R_visual/utils.R")

# Configuration
MODEL_TYPE <- "gpt-4o-mini"
BASE_DIR <- paste0("experiments/", MODEL_TYPE, "/paper/rq2")
OUTPUT_DIR <- paste0("visualization/figs/", MODEL_TYPE, "/paper/rq2")

# Condition naming
DIR_PREFIXES <- list(
  "r_wsc_F" = "r_wsc_F",
  "r_wsc_R" = "r_wsc_R",
  "rw_wsc_F" = "rw_wsc_F",
  "rw_wsc_R" = "rw_wsc_R"
)

CONDITIONS <- c("Rep", "Rep, Comm", "Rep+Warrant", "Rep+Warrant, Comm")
CONSTRAINTS <- c("policy_making", "pressure_quickprofits", "psychological-attack")

# X-axis label colors
COND_XCOLORS <- c(
  "Rep" = "#444444",
  "Rep, Comm" = "#4caf72",
  "Rep+Warrant" = "#1565c0",
  "Rep+Warrant, Comm" = "#1565c0"
)

# ============================================================
# Data Loading
# ============================================================

load_condition <- function(base_dir, constraint_key, cond) {
  prefix <- DIR_PREFIXES[[cond]]
  results_dir <- file.path(base_dir, paste0(prefix, "_", constraint_key))
  load_results_df(results_dir)
}

# ============================================================
# Figure: Deception by Constraint
# ============================================================

fig_deception_by_constraint <- function() {
  # Load data for each condition and constraint
  data <- list()
  
  for (constraint in CONSTRAINTS) {
    for (cond in CONDITIONS) {
      df <- load_condition(BASE_DIR, constraint, cond)
      if (nrow(df) > 0) {
        dec <- count_deceptions(df)
        data[[paste(constraint, cond)]] <- data.frame(
          constraint = constraint,
          condition = cond,
          deceptions = mean(dec, na.rm = TRUE)
        )
      }
    }
  }
  
  plot_data <- do.call(rbind, data)
  if (is.null(plot_data)) {
    message("[Fig] No data found, skipping.")
    return(NULL)
  }
  
  # Plot
  p <- ggplot(plot_data, aes(x = constraint, y = deceptions, fill = condition)) +
    geom_bar(position = position_dodge(), stat = "identity", alpha = 0.8) +
    scale_fill_manual(values = c(COLORS$bad_dark, COLORS$bad_mid, COLORS$good_mid, COLORS$good_dark)) +
    labs(x = "Constraint Type", y = "Deceptions (per run)",
         title = "Seller Communication Deception by Constraint") +
    setup_theme() +
    theme(legend.position = "top", legend.title = element_blank(),
          axis.text.x = element_text(angle = 45, hjust = 1))
  
  save_figure(p, file.path(OUTPUT_DIR, "rq2_seller_comm_deception_by_constraint.png"))
}

# ============================================================
# Figure: Profit Decomposition
# ============================================================

fig_profit_decomposition <- function() {
  data <- list()
  
  for (constraint in CONSTRAINTS) {
    for (cond in CONDITIONS) {
      df <- load_condition(BASE_DIR, constraint, cond)
      if (nrow(df) > 0) {
        honest_profit <- sum(df$is_honest * df$seller_profit, na.rm = TRUE)
        dishonest_profit <- sum(!df$is_honest * df$seller_profit, na.rm = TRUE)
        
        data[[paste(constraint, cond)]] <- data.frame(
          constraint = constraint,
          condition = cond,
          honest = honest_profit,
          dishonest = dishonest_profit
        )
      }
    }
  }
  
  plot_data <- do.call(rbind, data)
  if (is.null(plot_data)) return(NULL)
  
  plot_long <- pivot_longer(plot_data, cols = c(honest, dishonest),
                            names_to = "profit_type", values_to = "value")
  
  p <- ggplot(plot_long, aes(x = condition, y = value, fill = profit_type)) +
    geom_bar(position = "stack", stat = "identity", alpha = 0.8) +
    scale_fill_manual(values = c(COLORS$good_light, COLORS$bad_light),
                      labels = c("Honest profit", "Dishonest profit")) +
    labs(x = "Condition", y = "Total Seller Profit",
         title = "Profit Decomposition: Honest vs Dishonest") +
    setup_theme() +
    theme(legend.position = "top", legend.title = element_blank())
  
  save_figure(p, file.path(OUTPUT_DIR, "rq2_profit_decomposition_honest_vs_dishonest.png"))
}

# ============================================================
# Figure: Product Mix Appendix
# ============================================================

fig_product_mix <- function() {
  data <- list()
  
  for (constraint in CONSTRAINTS) {
    for (cond in CONDITIONS) {
      df <- load_condition(BASE_DIR, constraint, cond)
      if (nrow(df) > 0) {
        mix <- product_quality_counts(df)
        data[[paste(constraint, cond)]] <- data.frame(
          constraint = constraint,
          condition = cond,
          hq_auth = mix$hq_auth,
          lq_auth = mix$lq_auth,
          hq_cfeit = mix$hq_cfeit
        )
      }
    }
  }
  
  plot_data <- do.call(rbind, data)
  if (is.null(plot_data)) return(NULL)
  
  # Convert to percentages
  plot_data$total <- plot_data$hq_auth + plot_data$lq_auth + plot_data$hq_cfeit
  plot_data$hq_auth_pct <- plot_data$hq_auth / plot_data$total * 100
  plot_data$lq_auth_pct <- plot_data$lq_auth / plot_data$total * 100
  plot_data$hq_cfeit_pct <- plot_data$hq_cfeit / plot_data$total * 100
  
  plot_long <- pivot_longer(plot_data, cols = c(hq_auth_pct, lq_auth_pct, hq_cfeit_pct),
                            names_to = "product_type", values_to = "percentage")
  
  p <- ggplot(plot_long, aes(x = condition, y = percentage, fill = product_type)) +
    geom_bar(position = "stack", stat = "identity", alpha = 0.8) +
    scale_fill_manual(values = c(COLORS$counterfeit, COLORS$lq_auth, COLORS$hq_auth),
                      labels = c("HQ Counterfeit", "LQ Authentic", "HQ Authentic")) +
    labs(x = "Condition", y = "Share of Listed Products (%)",
         title = "Product Mix: All Listed Products") +
    setup_theme() +
    theme(legend.position = "top", legend.title = element_blank())
  
  save_figure(p, file.path(OUTPUT_DIR, "rq2_product_mix_appendix.png"))
}

# ============================================================
# Main
# ============================================================

main <- function() {
  dir.create(OUTPUT_DIR, recursive = TRUE, showWarnings = FALSE)
  
  message("RQ2: Generating Paper Figures (R version)")
  
  message("\n[Fig] Deception by Constraint...")
  fig_deception_by_constraint()
  
  message("\n[Fig] Profit Decomposition...")
  fig_profit_decomposition()
  
  message("\n[Fig] Product Mix...")
  fig_product_mix()
  
  message("\n[RQ2] All figures saved to:", OUTPUT_DIR)
}

main()
