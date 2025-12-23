# Run seller communication experiments with Fake channel
# Reputation only market
python ./example/run_single_config_experiment.py --experiment-id r_wsc_F --market-type reputation_only --communication seller --communication-channel-type Fake
python ./example/run_single_config_experiment.py --experiment-id r_wsc_R --market-type reputation_only --communication seller --communication-channel-type Real

# Reputation and warrant market
python ./example/run_single_config_experiment.py --experiment-id rw_wsc_F --market-type reputation_and_warrant --communication seller --communication-channel-type Fake
python ./example/run_single_config_experiment.py --experiment-id rw_wsc_R --market-type reputation_and_warrant --communication seller --communication-channel-type Real

python -m visualization.core.overseer_agent experiments/r_wsc_R.db \
    --model-platform openai \
    --model-type gpt-4o-mini \
    --temperature 0.1 \
    --output .cache/results.json

python3 visualization/RQ3_figs.py \
    --experiments-dir experiments \
    --output analysis/communication_effects/RQ3_buyer_communication_effects.png