# Run seller communication experiments with Fake channel
# Reputation only market
python ./example/run_single_config_experiment.py --experiment-id r_wsc_F --market-type reputation_only --communication seller --communication-channel-type Fake
python ./example/run_single_config_experiment.py --experiment-id r_wsc_R --market-type reputation_only --communication seller --communication-channel-type Real

# Reputation and warrant market
python ./example/run_single_config_experiment.py --experiment-id rw_wsc_F --market-type reputation_and_warrant --communication seller --communication-channel-type Fake
python ./example/run_single_config_experiment.py --experiment-id rw_wsc_R --market-type reputation_and_warrant --communication seller --communication-channel-type Real