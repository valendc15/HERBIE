# Herbie

Herbie is a Python script that automates the creation of a GitHub repository and pushes the local code to it.

## How it works

The script uses a Large Language Model (LLM) to orchestrate a series of tools to achieve its goal. The main logic is contained in the `herbie.py` file.

### Tools

Herbie defines two main tools:

*   `create_github_repo`: This tool takes a repository name, visibility (`public` or `private`), and a GitHub personal access token to create a new repository on GitHub.
*   `run_shell_command`: This tool executes any given shell command in the local environment.

### Workflow

1.  **User Input**: The script starts by prompting the user for the desired repository name and visibility.
2.  **GitHub Repository Creation**: It then uses the `create_github_repo` tool to create the new repository on GitHub.
3.  **Local Git Repository**: The script then uses the `run_shell_command` tool to perform the following git operations:
    *   Initializes a new git repository (`git init`).
    *   Adds all files to the staging area (`git add .`).
    *   Commits the changes with the message "Initial commit" (`git commit -m 'Initial commit'`).
    *   Adds the newly created GitHub repository as a remote origin.
    *   Pushes the local repository to the remote on GitHub.
4.  **Output**: Finally, the script prints the URL of the newly created GitHub repository.

## Installation

To use Herbie, you need to have Python installed, as well as the dependencies listed in the `requirements.txt` file.

1.  Clone the repository or download the files.
2.  Install the dependencies using pip:

```bash
pip install -r requirements.txt
```

## Configuration

Before running the script, you need to configure your environment variables.

1.  Create a `.env` file in the root of the project.
2.  Add the following variables to the `.env` file:

```
GEMINI_API_KEY="your_gemini_api_key_here"
GITHUB_TOKEN="your_github_token_here"
```

Replace `"your_gemini_api_key_here"` and `"your_github_token_here"` with your actual API keys.

## Usage

To run the script, simply execute the `herbie.py` file from your terminal:

```bash
python herbie.py
```

The script will then guide you through the process of creating your new GitHub repository.
