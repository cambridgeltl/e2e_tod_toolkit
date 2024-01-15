# ToD System Human Evaluation Tool

This directory is dedicated to human evaluations of task-oriented dialogue systems. This toolkit provides an integrated framework for evaluating the performance and user satisfaction of such systems.

This tool aims to streamline the process of human evaluation for dialogue systems, providing a platform for researchers and developers to evaluate the performance of their systems in real-world conversational scenarios.

## Repository Overview

The repository is organised into two primary components:

1. **`client`**: This module houses the frontend web interface of the human evaluation tool. It is developed as a React Application.

2. **`server`**: This module contains the backend server code necessary for the operation of the human evaluation tool.  It manages data processing, storage, and communication between the frontend interface and the dialogue systems being evaluated.



## Getting Started

Our tool is designed with an **out-of-the-box** capability, facilitated by full containerisation using docker and docker-compose. Try it following this [instruction](../deployment/README.md).



Before deployment, the web interface configuration file is located at [human_eval_tool/client/src/configs.js](client/src/configs.js). This file includes various settings, such as contact information, which can be customised as required.



## Development Setup

To facilitate development and circumvent CORS issues, we use a Dockerised nginx server. The setup process involves:

1. **Environment Configuration**:
   - Copy and modify the `.env` file from the deployment folder to both [client](client) and [server](server) directories.
   - Follow the instructions provided in the [Command line deployment and development deployment](../deployment/README.md#environment-setup-for-command-line-deployment-and-development) section.

2. **Nginx Deployment**:
   - In the deployment folder, deploy nginx with:
     ```
     bash deploy.sh --env=dev --component=tools --name {MODEL_NAME}
     ```
   - Replace `{MODEL_NAME}` with your chosen model name.

3. **Server Setup**:
   - Modify `MODEL_NAME` in `command_line.sh` to your model name.
   - Run `bash command_line.sh` to start the server on port 5000 or execute the commands in the script individually in a terminal.

4. **Client Development Setup**:
   - Inside the client folder, execute:
     ```
     npm install
     npm start
     ```

The web page and server should now be accessible at http://127.0.0.1:80 for testing.

## Extending the Tool

The tool is developed with customisation in mind. If you are looking to tailor this tool to fit your specific needs, such as dialogue evaluation or data collection, consider exploring the following resources:

1. **JavaScript and TypeScript**:
   - Learn the basics of [JavaScript](https://www.w3schools.com/js/) and [TypeScript](https://www.w3schools.com/typescript/index.php), the languages of our frontend.

2. **ReactJS**:
   - Have a look at [ReactJS](https://react.dev/learn).

3. **Ant Design**:
   - The web interface can be easily extend with any component from the [Ant Design](https://ant.design/components/overview) toolkit.

4. **Backend Development**:
   - To accommodate new functionalities, the Flask server's RESTful API may need modifications to handle additional requests from the frontend.

By leveraging these resources, customising the tool is a simple and manageable task. :relaxed:

---
