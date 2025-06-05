#### cron_ui
    A personal UI for Task scheduling on local laptop (UI for CRON).
    Manual launch or by CRON schedule.
    Easy to install eas


#### Setup and Running
```bash

    1.  **Clone the repository:**
        git clone <repository_url>
        cd cron_ui

        mkdir -p ztmp/scripts
        mkdir -p ztmp/log
        mkdir -p ztmp/zackup
        

    2.  **Install dependencies:**
        pip install -r requirements.txt

        ### if no config exist in ztmp
    3   cp --no-clobber  tasks.json  ztmp/tasks.json  #


    4.  **Run the application:**
        python cron_ui.py


        Then, open your web browser and go to the address provided (usually `http://127.0.0.1:9721`).



```

## Important Notes:
*   **Permissions:**
    *   You need permissions to modify your own crontab for scheduled tasks to work.
    *   The application requires write access to `tasks.json` in its directory to save task configurations.

*   **Shell for Script Execution:**
    *   The application executes scheduled scripts using the system's default shell (determined by the `SHELL` environment variable, typically falling back to `/bin/zsh` if not set). Ensure that the scripts are compatible with the default shell environment of the user running the `cron_ui.py` application.

```




```
Code




cron_calculate_next_run

tasks_load


script_content_textarea

layout_create_main_page

layout_create_manage_task

callback_load_script_content

callback_display_page

callback_save_task

callback_task_handle_actions

callback_show_main_page_alert

save_tasks_to_file

tasks_run

tasks_save_to_file

date_get_ymdhms

run_shell_script

os_get_process_info

os_get_process_usage_subprocess

task_add_cron

task_remove_cron

crontab_get_content

script_read_content

script_save_content


```