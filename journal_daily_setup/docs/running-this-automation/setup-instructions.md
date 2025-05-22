# Journal Automation Setup Instructions (Project-Contained)

Follow these steps to set up your journal automation to run both manually and automatically via launchd.

## Prerequisites

1. Make sure PocketFlow is installed:
   ```bash
   pip install pocketflow
   ```

## Project Setup

1. Create a bin directory inside your journal_automation folder:

   ```bash
   mkdir -p /Users/kdm/projects/digital-ext/business-os-automations/journal_daily_setup/bin
   ```

2. Save the `run_journal.sh` script to your project's bin directory:

   ```bash
   cp run_journal.sh /Users/kdm/projects/digital-ext/business-os-automations/journal_automation/bin/
   ```

3. Make the script executable:

   ```bash
   chmod +x /Users/kdm/projects/digital-ext/business-os-automations/journal_automation/bin/run_journal.sh
   ```

4. Create the log directory:
   ```bash
   mkdir -p ~/Library/Logs
   ```

## Setting up automatic scheduling with launchd

1. Save the plist file to your LaunchAgents directory:

   ```bash
   cp com.kdm.journal-automation.plist ~/Library/LaunchAgents/
   ```

2. Load the launchd job:

   ```bash
   launchctl load ~/Library/LaunchAgents/com.kdm.journal-automation.plist
   ```

3. Verify that it's loaded:
   ```bash
   launchctl list | grep journal
   ```

## Running manually

You can run the journal automation manually using:

### Option 1: Full path

```bash
/Users/kdm/projects/digital-ext/business-os-automations/journal_automation/bin/run_journal.sh
```

### Option 2: Create an alias (recommended)

Add this to your `~/.zshrc` file:

```bash
echo 'alias journal="/Users/kdm/projects/digital-ext/business-os-automations/journal_automation/bin/run_journal.sh"' >> ~/.zshrc
source ~/.zshrc
```

Then you can simply run:

```bash
journal
```

### Option 3: Run from project directory

```bash
cd /Users/kdm/projects/digital-ext/business-os-automations/journal_automation
./bin/run_journal.sh
```

## Advantages of this approach

- **Self-contained**: Everything related to journal automation is in one place
- **Version control friendly**: You can commit the entire setup including the runner script
- **Portable**: Easy to move or share the entire project
- **Clear ownership**: Obviously belongs to this specific automation project

## Troubleshooting

### Checking logs

If the automation doesn't run as expected, check the log files:

```bash
cat ~/Library/Logs/journal-automation.log
cat ~/Library/Logs/journal-automation.err
```

### Reloading after changes

If you modify the plist file, reload it:

```bash
launchctl unload ~/Library/LaunchAgents/com.kdm.journal-automation.plist
launchctl load ~/Library/LaunchAgents/com.kdm.journal-automation.plist
```

### Testing the launchd job

To test if the launchd job works without waiting for the scheduled time:

```bash
launchctl start com.kdm.journal-automation
```

### Uninstalling

To remove the automatic scheduling:

```bash
launchctl unload ~/Library/LaunchAgents/com.kdm.journal-automation.plist
rm ~/Library/LaunchAgents/com.kdm.journal-automation.plist
```
