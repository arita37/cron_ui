# cron_ui
A quick but working for local laptop Task Scheduler

## Setup and Running

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd cron_ui
    ```



2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    python cron_ui.py
    ```
    Then, open your web browser and go to the address provided (usually `http://127.0.0.1:9721`).

## Important Notes:

*   **Permissions:**
    *   You need permissions to modify your own crontab for scheduled tasks to work.
    *   The application requires write access to `tasks.json` in its directory to save task configurations.

*   **Shell for Script Execution:**
    *   The application executes scheduled scripts using the system's default shell (determined by the `SHELL` environment variable, typically falling back to `/bin/sh` if not set). Ensure that the scripts are compatible with the default shell environment of the user running the `cron_ui.py` application.

```
