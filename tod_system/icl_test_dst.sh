# Example script for testing ICL-based DST models (Note: This script can also be used for FT-based DST models, but expect slower performance due to the batch size being set to 1). Please ensure to modify the relevant configuration file according to your specific requirements.

#PYTHONPATH=$(pwd) python ./agent/icl_test_dst.py -c ./agent/config/example_fthuggingface.cfg
PYTHONPATH=$(pwd) python ./agent/icl_test_dst.py -c ./agent/config/example_iclopenai.cfg