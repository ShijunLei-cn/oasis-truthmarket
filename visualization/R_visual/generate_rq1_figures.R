#!/usr/bin/env Rscript
# ============================================================
# RQ1 Figures — Warrant vs. Reputation-Only Mechanism
# 
# Generates:
# - rq1_warrant_vs_rep_deception_and_profit.png
# - rq1_exit_loophole_vulnerability.png
# - rq1_product_mix_appendix.png
# ============================================================

library(ggplot2)
library(dplyr)
library(tidyr)
library(jsonlite)

# Source utilities
source("visualization/R_visual/utils.R")

# Configuration
MODEL_TYPE <- "gpt-4o-mini"
BASE_DIR <- paste0("experiments/", MODEL_TYPE, "/paper")
OUTPUT_DIR <- paste0("visualization/figs/", MODEL_TYPE, "/paper/rq1")

# Condition labels
LABEL_R <- "Rep"
LABEL_RW <- "Rep+Warrant"

# ============================================================
# Figure 1: Seller Profit & Deceptions
# ============================================================

fig1_profit_and_deceptions <- function() {
  # Load data
  df_r <- load_results_df(file.path(BASE_DIR, "rq1/r_wo"))
  df_rw <- load_results_df(file.path(BASE_DIR, "rq1/rw_wo"))
  
  if (nrow(df_r) == 0 || nrow(df_rw) == 0) {
    message("[Fig1] Missing data, skipping.")
    return(NULL)
  }
  
  # Calculate per-run metrics
  profit_r <- sum_seller_profit(df_r)
  profit_rw <- sum_seller_profit(df_rw)
  dec_r <- count_deceptions(df_r)
  dec_rw <- count_deceptions(df_rw)
  
  # Statistical tests
  p_profit <- mannwhitney_p(profit_r, profit_rw)
  p_dec <- mannwhitney_p(dec_r, dec_rw)
  
  # Prepare data for plotting
  profit_data <- data.frame(
    value = c(profit_r, profit_rw),
    condition = c(rep(LABEL_R, length(profit_r)), rep(LABEL_RW, length(profit_rw)))
  )
  
  dec_data <- data.frame(
    value = c(dec_r, dec_rw),
    condition = c(rep(LABEL_R, length(dec_r)), rep(LABEL_RW, length(dec_rw)))
  )
  
  # Create figure with 3 panels
  # Panel A: Profit
  p_profit <- ggplot(profit_data, aes(x = condition, y = value, fill = condition)) +
    geom_boxplot(alpha = 0.7) +
    scale_fill_manual(values = c(COLORS$good_mid, COLORS$good_dark)) +
    labs(x = "Condition", y = "Total Seller Profit (per run)", title = "(a) Seller Profit") +
    setup_theme() +
    theme(legend.position = "none")
  
  # Panel B: Deceptions
  p_dec <- ggplot(dec_data, aes(x = condition, y = value, fill = condition)) +
    geom_boxplot(alpha = 0.7) +
    scale_fill_manual(values = c(COLORS$bad_dark, COLORS$neutral)) +
    labs(x = "Condition", y = "Deceptive Transactions (per run)", title = "(b) Deceptions") +
    setup_theme() +
    theme(legend.position = "none")
  
  # Save figure
  png(file.path(OUTPUT_DIR, "rq1_warrant_vs_rep_deception_and_profit.png"), 
      width = 11, height = 3.8, units = "in", res = 300)
  print(p_profit)
  dev.off()
  
  message(paste("[Fig1] p_profit =", round(p_profit, 4), ", p_dec =", round(p_dec, 4)))
}

# ============================================================
# Figure 2: Vulnerability Probe Detection Rates
# ============================================================

VULN_KEYS <- c("initial_window", "reputation_lag", "value_imbalance", "reentry", "exit_strategy")
VULN_LABELS <- c("Initial\nWindow", "Reputation\nLag", "Value\nImbalance", "Reentry", "Exit\nStrategy")

fig2_probe_and_product_mix <- function() {
  # Load probe data
  probe_r <- load_probes_df(file.path(BASE_DIR, "rq1/r_wo"))
  probe_rw <- load_probes_df(file.path(BASE_DIR, "rq1/rw_wo"))
  
  if (nrow(probe_r) == 0 || nrow(probe_rw) == 0) {
    message("[Fig2] No probe data found, skipping.")
    return(NULL)
  }
  
  # Load results for product mix
  df_r <- load_results_df(file.path(BASE_DIR, "rq1/r_wo"))
  df_rw <- load_results_df(file.path(BASE_DIR, "rq1/rw_wo"))
  
  # Calculate probe rates by vulnerability type
  calc_probe_rates <- function(probe_df) {
    probe_df %>%
      group_by(run_id, vulnerability_type) %>%
      summarise(rate = mean(manipulation_detected, na.rm = TRUE), .groups = "drop") %>%
      group_by(vulnerability_type) %>%
      summarise(mean_rate = mean(rate, na.rm = TRUE) * 100,
                sd_rate = sd(rate, na.rm = TRUE) * 100, .groups = "drop")
  }
  
  rates_r <- calc_probe_rates(probe_r)
  rates_rw <- calc_probe_rates(probe_rw)
  
  rates_r$condition <- LABEL_R
  rates_rw$condition <- LABEL_RW
  
  probe_data <- rbind(rates_r, rates_rw)
  probe_data$vuln_label <- factor(probe_data$vulnerability_type, levels = VULN_KEYS, labels = VULN_LABELS)
  
  # Panel A: Vulnerability probe rates
  p_probe <- ggplot(probe_data, aes(x = vuln_label, y = mean_rate, fill = condition)) +
    geom_bar(position = position_dodge(), stat = "identity", alpha = 0.8) +
    geom_errorbar(aes(ymin = mean_rate - sd_rate, ymax = mean_rate + sd_rate),
                  position = position_dodge(0.9), width = 0.3) +
    scale_fill_manual(values = c(COLORS$bad_dark, COLORS$bad_mid)) +
    labs(x = "Vulnerability Type", y = "Manipulation Detection Rate (%)",
         title = "(a) Manipulation Detection Rate by Vulnerability") +
    setup_theme() +
    theme(legend.position = "top", legend.title = element_blank())
  
  # Panel B: Product mix (stacked bar)
  calc_product_mix <- function(df) {
    if (nrow(df) == 0) return(NULL)
    
    q_col <- grep("quality|actual_quality|true_quality", names(df), value = TRUE)[1]
    a_col <- "advertised_quality"
    
    if (is.na(q_col)) return(NULL)
    
    df[[q_col]] <- toupper(df[[q_col]])
    df[[a_col]] <- toupper(df[[a_col]])
    
    hq_auth <- sum(df[[a_col]] == "HQ" & df[[q_col]] == "HQ", na.rm = TRUE)
    lq_auth <- sum(df[[a_col]] == "LQ" & df[[q_col]] == "LQ", na.rm = TRUE)
    hq_cfeit <- sum(df[[a_col]] == "HQ" & df[[q_col]] == "LQ", na.rm = TRUE)
    total <- hq_auth + lq_auth + hq_cfeit
    
    data.frame(
      hq_auth = hq_auth / total * 100,
      lq_auth = lq_auth / total * 100,
      hq_cfeit = hq_cfeit / total * 100
    )
  }
  
  mix_r <- calc_product_mix(df_r)
  mix_rw <- calc_product_mix(df_rw)
  
  mix_data <- data.frame(
    condition = c(LABEL_R, LABEL_RW),
    hq_auth = c(mix_r$hq_auth, mix_rw$hq_auth),
    lq_auth = c(mix_r$lq_auth, mix_rw$lq_auth),
    hq_cfeit = c(mix_r$hq_cfeit, mix_rw$hq_cfeit)
  )
  
  mix_long <- pivot_longer(mix_data, cols = c(hq_auth, lq_auth, hq_cfeit),
                           names_to = "product_type", values_to = "percentage")
  mix_long$product_type <- factor(mix_long$product_type,
                                   levels = c("hq_cfeit", "lq_auth", "hq_auth"),
                                   labels = c("HQ Counterfeit", "LQ Authentic", "HQ Authentic"))
  
  p_mix <- ggplot(mix_long, aes(x = condition, y = percentage, fill = product_type)) +
    geom_bar(position = "stack", stat = "identity", alpha = 0.8) +
    scale_fill_manual(values = c(COLORS$counterfeit, COLORS$lq_auth, COLORS$hq_auth)) +
    labs(x = "Condition", y = "Share of Sold Products (%)",
         title = "(b) Sold Product Mix") +
    setup_theme() +
    theme(legend.position = "top", legend.title = element_blank())
  
  # Save combined figure
  png(file.path(OUTPUT_DIR, "rq1_exit_loophole_vulnerability.png"),
      width = 10.5, height = 4.0, units = "in", res = 300)
  # Simple 2-panel layout
  par(mfrow = c(1, 2), mar = c(4, 4, 2, 1))
  print(p_probe)
  print(p_mix)
  dev.off()
  
  message("[Fig2] Saved")
}

# ============================================================
# Main
# ============================================================

main <- function() {
  dir.create(OUTPUT_DIR, recursive = TRUE, showWarnings = FALSE)
  
  message(paste(rep("=", 60), collapse = ""))
  message("RQ1: Generating Paper Figures (R version)")
  message(paste(rep("=", 60), collapse = ""))
  
  message("\n[Fig1] Seller Profit & Deceptions...")
  fig1_profit_and_deceptions()
  
  message("\n[Fig2] Vulnerability Probe + Product Mix...")
  fig2_probe_and_product_mix()
  
  message("\n[RQ1] All figures saved to:", OUTPUT_DIR)
}

main()
