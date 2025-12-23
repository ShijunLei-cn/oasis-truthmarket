# Run buyer communication experiments with Fake channel
# Reputation only market
python ./example/run_single_config_experiment.py --experiment-id r_wbc_F --market-type reputation_only --communication buyer --communication-channel-type Fake
python ./example/run_single_config_experiment.py --experiment-id r_wbc_R --market-type reputation_only --communication buyer --communication-channel-type Real

# Reputation and warrant market
python ./example/run_single_config_experiment.py --experiment-id rw_wbc_F --market-type reputation_and_warrant --communication buyer --communication-channel-type Fake
python ./example/run_single_config_experiment.py --experiment-id rw_wbc_R --market-type reputation_and_warrant --communication buyer --communication-channel-type Real

