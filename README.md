#### cron_ui
    A personal UI for Task scheduling on local laptop (UI for CRON).
    Manual launch or by CRON schedule.
    Easy to install eas


![image](https://github.com/user-attachments/assets/9cba2d68-0cae-4ee0-a5c7-80327b2791a8)


#### Setup and Running
```bash

1.  **Clone the repository:**
    git clone https://github.com/arita37/cron_ui.git
    cd cron_ui

2.  **Install dependencies:**
    pip install -r requirements.txt

3.  **Run the application:**
    python cron_ui.py


Then, open your web browser and go to the address provided (usually `http://127.0.0.1:9721`).

```


## Important Notes:
*   **Permissions:**
    *   You need permissions to modify your own crontab for scheduled tasks to work.
    *   The application requires write access to `tasks.json` in its directory to save task configurations.

*   **Shell for Script Execution:**
    *   The application executes scheduled scripts using the system's default shell (determined by the `SHELL` environment variable, typically falling back to `/bin/sh` if not set). Ensure that the scripts are compatible with the default shell environment of the user running the `cron_ui.py` application.

```







