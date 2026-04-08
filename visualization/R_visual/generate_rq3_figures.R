#!/usr/bin/env Rscript
# ============================================================
# RQ3 Figures — Buyer Communication & Collective Defense
# 
# Generates:
# - rq3_buyer_comm_market_outcomes.png
# - rq3_round_adaptation_appendix.png
# ============================================================

library(ggplot2)
library(dplyr)
library(tidyr)

source("visualization/R_visual/utils.R")

# Configuration
MODEL_TYPE <- "gpt-4o-mini"
BASE_DIR <- paste0("experiments/", MODEL_TYPE, "/paper/rq3")
OUTPUT_DIR <- paste0("visualization/figs/", MODEL_TYPE, "/paper/rq3")

# Condition labels
DIRS <- c(
  "Rep" = "r_wbc_F",
  "Rep, +BComm" = "r_wbc_R",
  "Rep+Warrant" = "rw_wbc_F",
  "Rep+Warrant, +BComm" = "rw_wbc_R"
)

PAIRS <- list(
  c("Rep", "Rep, +BComm", "Rep"),
  c("Rep+Warrant", "Rep+Warrant, +BComm", "Rep+Warrant")
)

# Mechanism colors (using unified palette)
MECH_COLORS_BASE <- c(COLORS$rep_mid, COLORS$warrant_mid)
MECH_COLORS_COMM <- c(COLORS$rep_dark, COLORS$warrant_dark)

# ============================================================
# Data Loading
# ============================================================

load_condition <- function(base_dir, label) {
  results_dir <- file.path(base_dir, DIRS[label])
  load_results_df(results_dir)
}

# ============================================================
# Figure: 2x2 Multi-metric Comparison
# ============================================================

fig7_market_outcomes <- function() {
  # Load all conditions
  data <- list()
  for (label in names(DIRS)) {
    df <- load_condition(BASE_DIR, label)
    if (nrow(df) > 0) {
      data[[label]] <- data.frame(
        label = label,
        profit = mean(sum_seller_profit(df)),
        utility = mean(sum_buyer_utility(df)),
        transactions = mean(aggregate(transactions ~ run_id, data = df, FUN = sum)$transactions),
        deceptions = mean(count_deceptions(df))
      )
    }
  }
  
  plot_data <- do.call(rbind, data)
  if (is.null(plot_data)) {
    message("[Fig7] No data found, skipping.")
    return(NULL)
  }
  
  # Reshape for plotting
  plot_long <- pivot_longer(plot_data, cols = c(profit, utility, transactions, deceptions),
                            names_to = "metric", values_to = "value")
  
  # Metric labels
  metric_labels <- c(
    "profit" = "Seller Profit",
    "utility" = "Buyer Utility",
    "transactions" = "Transactions",
    "deceptions" = "Deceptions"
  )
  
  # Color mapping
  get_colors <- function(label) {
    has_comm <- grepl("\\+BComm", label)
    is_warrant <- grepl("Warrant", label)
    
    if (is_warrant) {
      if (has_comm) COLORS$warrant_dark else COLORS$warrant_mid
    } else {
      if (has_comm) COLORS$rep_dark else COLORS$rep_mid
    }
  }
  
  plot_long$color <- sapply(plot_long$label, get_colors)
  
  # 2x2 panel plot
  p <- ggplot(plot_long, aes(x = label, y = value, fill = label)) +
    geom_bar(stat = "identity", alpha = 0.8) +
    scale_fill_manual(values = setNames(plot_long$color, plot_long$label)) +
    facet_wrap(~ metric, scales = "free_y", labeller = as_labeller(metric_labels)) +
    labs(x = "Condition", y = "Value", 
         title = "Adversarial Design: Buyer Communication vs Coordinated Seller Deception") +
    setup_theme() +
    theme(legend.position = "top", legend.title = element_blank(),
          axis.text.x = element_text(angle = 45, hjust = 1))
  
  save_figure(p, file.path(OUTPUT_DIR, "rq3_buyer_comm_market_outcomes.png"), width = 8.5, height = 6)
}

# ============================================================
# Figure: Per-round Buyer Utility
# ============================================================

fig8_round_utility <- function() {
  # Load data
  df_rep <- load_condition(BASE_DIR, "Rep")
  df_repc <- load_condition(BASE_DIR, "Rep, +BComm")
  df_rw <- load_condition(BASE_DIR, "Rep+Warrant")
  df_rwc <- load_condition(BASE_DIR, "Rep+Warrant, +BComm")
  
  # Calculate per-round utility
  calc_round_utility <- function(df) {
    if (nrow(df) == 0) return(NULL)
    df %>%
      group_by(run_id, round_num) %>%
      summarise(utility = sum(buyer_utility, na.rm = TRUE), .groups = "drop") %>%
      group_by(round_num) %>%
      summarise(mean_utility = mean(utility, na.rm = TRUE),
                sd_utility = sd(utility, na.rm = TRUE), .groups = "drop")
  }
  
  round_rep <- calc_round_utility(df_rep)
  round_repc <- calc_round_utility(df_repc)
  round_rw <- calc_round_utility(df_rw)
  round_rwc <- calc_round_utility(df_rwc)
  
  # Combine for Rep mechanism
  rep_data <- rbind(
    cbind(round_rep, condition = "Rep"),
    cbind(round_repc, condition = "Rep, +BComm")
  )
  
  # Combine for RW mechanism
  rw_data <- rbind(
    cbind(round_rw, condition = "Rep+Warrant"),
    cbind(round_rwc, condition = "Rep+Warrant, +BComm")
  )
  
  # Plot Rep mechanism
  p_rep <- ggplot(rep_data, aes(x = round_num, y = mean_utility, color = condition)) +
    geom_line() +
    geom_point() +
    geom_errorbar(aes(ymin = mean_utility - sd_utility, ymax = mean_utility + sd_utility),
                  width = 0.3) +
    scale_color_manual(values = c(COLORS$rep_mid, COLORS$rep_dark)) +
    labs(x = "Round", y = "Buyer Utility", title = "Rep Mechanism") +
    setup_theme() +
    theme(legend.position = "top")
  
  # Plot RW mechanism
  p_rw <- ggplot(rw_data, aes(x = round_num, y = mean_utility, color = condition)) +
    geom_line() +
    geom_point() +
    geom_errorbar(aes(ymin = mean_utility - sd_utility, ymax = mean_utility + sd_utility),
                  width = 0.3) +
    scale_color_manual(values = c(COLORS$warrant_mid, COLORS$warrant_dark)) +
    labs(x = "Round", y = "Buyer Utility", title = "Rep+Warrant Mechanism") +
    setup_theme() +
    theme(legend.position = "top")
  
  # Save combined
  png(file.path(OUTPUT_DIR, "rq3_round_adaptation_appendix.png"),
      width = 10, height = 4, units = "in", res = 300)
  par(mfrow = c(1, 2), mar = c(4, 4, 2, 1))
  print(p_rep)
  print(p_rw)
  dev.off()
  
  message("[Fig8] Saved")
}

# ============================================================
# Main
# ============================================================

main <- function() {
  dir.create(OUTPUT_DIR, recursive = TRUE, showWarnings = FALSE)
  
  message("RQ3: Generating Paper Figures (R version)")
  
  message("\n[Fig7] Market Outcomes...")
  fig7_market_outcomes()
  
  message("\n[Fig8] Round Adaptation...")
  fig8_round_utility()
  
  message("\n[RQ3] All figures saved to:", OUTPUT_DIR)
}

main()
