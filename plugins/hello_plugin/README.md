# Hello Plugin

A simple example plugin for Terminal AI Assistant that provides greeting and system information commands.

## Features

- Greeting commands with random responses
- System information display
- Programming jokes
- Command interception example

## Usage

Once the plugin is enabled, you can use the following commands:

- `hello [name]` - Say hello, optionally with a name
- `systeminfo [mode]` - Show system information (modes: brief, detailed, memory, cpu, disk)
- `joke` - Get a random programming joke

## Examples

```
> hello
Hi there! Ready to help! 👋
I'm the hello_plugin, ready to assist you!

> hello world
Hello, world! 👋
Greetings from the hello_plugin.

> systeminfo
System: Windows 10 (10.0.19045)
Machine: AMD64
Processor: Intel64 Family 6 Model 142 Stepping 10, GenuineIntel

> systeminfo detailed
System: Windows 10 (10.0.19045)
Machine: AMD64
Processor: Intel64 Family 6 Model 142 Stepping 10, GenuineIntel

Memory Usage:
  Total: 16.00 GB
  Available: 8.23 GB
  Used: 7.77 GB (48.6%)

CPU Usage:
  Core 1: 5.6%
  Core 2: 3.2%
  Core 3: 11.7%
  Core 4: 2.9%
  Overall: 5.8%

Disk Usage:
  C:\ (C:\):
    Total: 237.97 GB
    Used: 180.88 GB (76.0%)
    Free: 57.09 GB

> joke
Why do programmers prefer dark mode? Because light attracts bugs!
```

## Command Interception

This plugin also demonstrates how plugins can intercept and modify commands:

- Any command starting with `echo hello` will have " (plugin intercepted)" appended to it
- All successful commands will have "[Processed by hello_plugin]" added to their output

These features demonstrate how plugins can modify input and output of the terminal assistant. 