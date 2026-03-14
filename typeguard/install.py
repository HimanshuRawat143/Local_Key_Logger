"""
TypeGuard Installer — Configures Windows auto-start via Task Scheduler.

Usage:
    python install.py              Install auto-start (Python mode)
    python install.py --uninstall  Remove auto-start
    TypeGuard.exe --install        Install auto-start (EXE mode)
    TypeGuard.exe --uninstall      Remove auto-start (EXE mode)
"""
import os
import sys
import subprocess
import ctypes


APP_NAME = "TypeGuard"
TASK_NAME = "TypeGuard_AutoStart"


def is_admin() -> bool:
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def request_admin():
    """Re-launch this script with admin privileges using UAC prompt."""
    try:
        if getattr(sys, 'frozen', False):
            # Running as .exe
            exe = sys.executable
            params = " ".join(sys.argv[1:])
        else:
            # Running as Python script
            exe = sys.executable
            params = f'"{os.path.abspath(__file__)}" ' + " ".join(sys.argv[1:])

        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, params, None, 1
        )
        sys.exit(0)
    except Exception as e:
        print(f"Could not elevate privileges: {e}")
        sys.exit(1)


def get_run_command() -> tuple[str, str, str]:
    """
    Return (program, arguments, working_dir) for the scheduled task.
    Detects if running as bundled .exe or as Python script.
    """
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller .exe
        exe_path = os.path.abspath(sys.executable)
        return exe_path, "", os.path.dirname(exe_path)
    else:
        # Running as Python script
        python_path = sys.executable
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return python_path, "-m typeguard.main", script_dir


def install():
    """Create a Windows scheduled task to run TypeGuard at user logon."""
    if not is_admin():
        print("⚡ Administrator privileges required. Requesting elevation...")
        request_admin()
        return

    program, arguments, working_dir = get_run_command()

    print(f"Installing {APP_NAME} auto-start...")
    print(f"  Program:     {program}")
    if arguments:
        print(f"  Arguments:   {arguments}")
    print(f"  Working Dir: {working_dir}")
    print()

    # Use PowerShell to create the task WITH a working directory
    # (schtasks.exe doesn't support working directory, PowerShell does)
    if arguments:
        execute_path = program
        execute_args = arguments
    else:
        execute_path = program
        execute_args = ""

    # Escape paths for PowerShell
    execute_path_escaped = execute_path.replace("'", "''")
    execute_args_escaped = execute_args.replace("'", "''")
    working_dir_escaped = working_dir.replace("'", "''")

    ps_script = f"""
        $ErrorActionPreference = 'Stop'
        try {{
            # Remove existing task if present
            Unregister-ScheduledTask -TaskName '{TASK_NAME}' -Confirm:$false -ErrorAction SilentlyContinue

            # Create action with working directory
            $action = New-ScheduledTaskAction -Execute '{execute_path_escaped}' -Argument '{execute_args_escaped}' -WorkingDirectory '{working_dir_escaped}'

            # Trigger on user logon with 10-second delay
            $trigger = New-ScheduledTaskTrigger -AtLogOn
            $trigger.Delay = 'PT10S'

            # Settings: allow on battery, don't stop on battery, no time limit
            $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 0)

            # Register the task
            Register-ScheduledTask -TaskName '{TASK_NAME}' -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null

            Write-Output 'SUCCESS'
        }} catch {{
            Write-Output "FAILED: $_"
        }}
    """

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        capture_output=True,
        text=True,
    )

    output = result.stdout.strip()

    if "SUCCESS" in output:
        print("✅ Auto-start installed successfully!")
        print(f"   Task Name: {TASK_NAME}")
        print(f"   TypeGuard will start automatically when you log in.")
        print()
        print("   To verify, open Task Scheduler and look for:")
        print(f"   '{TASK_NAME}' in the Task Scheduler Library.")
    else:
        print("❌ Failed to create scheduled task.")
        error_msg = output if output else result.stderr
        print(f"   Error: {error_msg}")


def uninstall():
    """Remove the TypeGuard scheduled task."""
    if not is_admin():
        print("⚡ Administrator privileges required. Requesting elevation...")
        request_admin()
        return

    print(f"Removing {APP_NAME} auto-start...")

    ps_script = f"""
        $ErrorActionPreference = 'Stop'
        try {{
            Unregister-ScheduledTask -TaskName '{TASK_NAME}' -Confirm:$false
            Write-Output 'SUCCESS'
        }} catch {{
            Write-Output "FAILED: $_"
        }}
    """

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        capture_output=True,
        text=True,
    )

    if "SUCCESS" in result.stdout:
        print("✅ Auto-start removed successfully!")
    else:
        print("❌ Task not found or could not be removed.")
        print(f"   {result.stdout.strip() or result.stderr.strip()}")


def main():
    if "--uninstall" in sys.argv:
        uninstall()
    elif "--install" in sys.argv or (not getattr(sys, 'frozen', False)):
        install()


if __name__ == "__main__":
    main()
