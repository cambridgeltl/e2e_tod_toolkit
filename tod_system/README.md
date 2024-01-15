# Multilingual E2E ToD System Development and Evaluation

This directory contains the code necessary for both training and evaluating dialogue systems. Our toolkit offers support for two major methodologies: 1) **fine-tuning pretrained language models**, and 2) **in-context learning with large language models**.

This directory is primarily dedicated to support **automatic evaluation** of dialogue systems. Additionally, it includes scripts for setting up microservices for human evaluation.

## Repository Overview

This directory is structured into eight modules and a handful of scripts:

1. **`agent`**: Contains the source code for systems and system components (e.g., DST models and RG models) implemented with in-context learning with large language models. It also contains an agent class, which user could construct an agent to chat.

2. **`dataset`**: Contains dataloaders, database, and utilities function mostly and specific for Multi3WOZ dataset and other datasets from MultiWOZ family.

3. **`dst`**: Contains training and evaluation scripts for fine-tuning-based DST models.

4. **`e2e`**: Contains evaluation scripts for fine-tuning-based E2E systems.

5. **`evaluation`**: Contains automatic evaluation metrics for DST, RG, and E2E tasks.

6. **`human_eval_service`**: Contains scripts for setting up microservices for human evaluation.

7. **`rg`**: Contains training and evaluation scripts for fine-tuning-based RG models.

8. **`tests`**: Contains unit tests for the MultiWOZ Database Interface, Dataset interface, and Multi3WOZ Metrics.

## Get Started

To recreate the Conda environment used for this project, run the following command:

```bash
conda env create -f environment.yml
```

Then activate the conda environment:

```bash
conda activate tod
```

Before running any experiments, please also download our Multi3WOZ dataset:

```bash
bash download_data.sh
```

Now, you are ready to train and evaluate dialogue systems! 🥳

## How to Use

This toolkit employs a configuration-based script execution approach. This means most scripts require a configuration file as an argument. 

**Important**: Before running any experiments, please ensure to modify the configuration file according to your environment. Key parameters like `project_root_path` must be set correctly to reflect your project's setup.

For example, to train a DST model, you would use a command like the following, specifying the configuration file:

```bash
PYTHONPATH=$(pwd) python ./dst/ft_train_dst.py -c ./dst/config/example.cfg
```

This command sets the current directory as part of the Python path and executes the training script with a specified configuration file.

To evaluate the model you have just trained, simply use the same configuration file. For example:

```bash
PYTHONPATH=$(pwd) python ./dst/ft_test_dst.py -c ./dst/config/example.cfg
```

This approach ensures a consistent mapping between models/systems and their configuration files.


## Example Scripts

Explore the functionalities provided in our toolkit through these example scripts:

1. **`ft_train_dst.sh`**: Example script for training the FT-based DST models.

2. **`ft_test_dst.sh`**: Example script for testing the FT-based DST models.

3. **`ft_train_rg.sh`**: Example script for training the FT-based RG models.

4. **`ft_test_e2e.sh`**: Example script for testing the FT-based E2E systems.

5. **`icl_test_dst.sh`**: Example script for training the ICL-based DST models.

6. **`icl_test_rg.sh`**: Example script for training the ICL-based RG models.

7. **`icl_test_e2e.sh`**: Example script for training the ICL-based E2E systems.

8. **`run_agent.sh`**: Example script to run a chat agent.

For details on setting up microservices for human evaluation, refer to the relevant section below.

## Setting Up Model Servers for Human Evaluation without Docker

The model servers are tailored to work seamlessly with the human evaluation tool. These servers are implemented as celery workers service. For command-line deployment, follow these steps:


### Initial Setup

- **Model Connector Setup**:
  Begin by following the instructions: [Model Connector Setup ](../deployment/README.md#model-connector-for-command-line)

- **Environment File Configuration**:
  Modify the `.env` file in the deployment folder, then copy it to [human_eval_service](human_eval_service). Place your model config file into [human_eval_service/config](human_eval_service/config) with your model name.


- **Conda Environment Creation**:
  After completing the above steps, create a Conda environment by running the following command in your terminal:
  ```bash
  conda env create -f ./environment.yml
  ```
  

### For production

1. **Download Data**:
    To begin, download the necessary data by running the following command:
    ```bash
    bash download_data.sh
    ```

2. **Setting up Microservices**:
    If you plan to use microservices with both `rst` and `rg`, follow these steps:

    - Modify the `MODEL_NAME` in both [terminal_deploy_dst.sh](terminal_deploy_dst.sh) and [terminal_deploy_rg.sh](terminal_deploy_rg.sh).
    
    - Open one terminal window and run the following command:
      ```bash
      bash -i ./terminal_deploy_dst.sh
      ```
      This will start the microservice for DST models.

    - Open another terminal window and run the following command:
      ```bash
      bash -i ./terminal_deploy_rg.sh
      ```
      This will start the microservice for RG models.

    Now, you have running RG and DST models connected to the Redis model connector.

3. **Implement Your Own End-to-End System**:
    If you plan to implement your own end-to-end system and want to use this evaluation service, follow these steps:

    - Implement your own end-to-end system in a file named [your_own_cool_e2e_system.py](human_eval_service/your_own_cool_e2e_system.py).
    - Fulfill the `build_own_system` method in [human_eval_service/model_loader.py](human_eval_service/model_loader.py) to configure your system.

4. **Deploy Your Model**:
    - Modify the `MODEL_NAME` in [terminal_deploy_e2e.sh](terminal_deploy_e2e.sh).
    - Run the following command to deploy your model and start a Celery worker:
      ```bash
      bash -i ./terminal_deploy_e2e.sh
      ```
    
### For Development

In addition to the production setup, we offer a FastAPI tester server for quickly testing your model Celery worker. This tool is useful if you are utilising rg and dst microservices. For your own e2e system server, you may need to tailor the tester program accordingly.

To start the FastAPI tester, execute the following command:

```bash
bash -i fastAPI.sh
```

## Installing Llama.CPP for this Project

To utilise the Llama.CPP package for on-device large language model inference in this project, please follow the official Llama.CPP GitHub repository and install the Python bindings: [lama-cpp-python GitHub Repository](https://github.com/abetlen/llama-cpp-python/blob/main/README.md).

---
