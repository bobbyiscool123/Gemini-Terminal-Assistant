"""
Command Chain Module
Provides functionality to chain multiple commands together with conditional execution
"""
import os
import re
import time
import subprocess
from typing import List, Dict, Any, Union, Optional, Tuple, Callable

class CommandStep:
    """Represents a single step in a command chain"""
    
    def __init__(self, command: str, name: str = None, 
                 condition: str = None, timeout: int = 30,
                 shell: bool = True, cwd: str = None):
        """Initialize a command step"""
        self.command = command
        self.name = name or f"Step_{hash(command) % 10000}"
        self.condition = condition
        self.timeout = timeout
        self.shell = shell
        self.cwd = cwd
        self.result = None
        self.status = "pending"  # pending, running, success, error, skipped
        self.start_time = None
        self.end_time = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to a dictionary"""
        return {
            "command": self.command,
            "name": self.name,
            "condition": self.condition,
            "timeout": self.timeout,
            "shell": self.shell,
            "cwd": self.cwd,
            "status": self.status,
            "result": self.result
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandStep':
        """Create a step from a dictionary"""
        step = cls(
            command=data.get("command", ""),
            name=data.get("name"),
            condition=data.get("condition"),
            timeout=data.get("timeout", 30),
            shell=data.get("shell", True),
            cwd=data.get("cwd")
        )
        step.status = data.get("status", "pending")
        step.result = data.get("result")
        return step

class CommandChain:
    """Manages a chain of commands with conditional execution"""
    
    # Class variable to store all chains
    _chains = {}
    
    def __init__(self, name: str = None, working_dir: str = None):
        """Initialize a command chain"""
        self.name = name or f"Chain_{int(time.time())}"
        self.steps: List[CommandStep] = []
        self.working_dir = working_dir or os.getcwd()
        self.variables = {}
        self.on_step_start = None
        self.on_step_complete = None
        self.on_chain_complete = None
        
        # Register this chain in the class storage
        CommandChain._chains[self.name] = self
        
    def add_step(self, step: Union[CommandStep, str], **kwargs) -> CommandStep:
        """Add a step to the chain"""
        if isinstance(step, str):
            step = CommandStep(step, **kwargs)
        self.steps.append(step)
        return step
        
    def remove_step(self, index: int) -> bool:
        """Remove a step by index"""
        if 0 <= index < len(self.steps):
            del self.steps[index]
            return True
        return False
        
    def clear_steps(self) -> None:
        """Clear all steps"""
        self.steps = []
        
    def set_variable(self, name: str, value: str) -> None:
        """Set a variable for substitution in commands"""
        self.variables[name] = value
        
    def get_variable(self, name: str) -> Optional[str]:
        """Get a variable value"""
        return self.variables.get(name)
        
    def expand_variables(self, text: str) -> str:
        """Expand variables in a text string"""
        result = text
        
        # Replace ${var} style variables
        for name, value in self.variables.items():
            pattern = r'\${' + re.escape(name) + r'}'
            result = re.sub(pattern, str(value), result)
            
        # Replace $var style variables
        for name, value in self.variables.items():
            pattern = r'\$' + re.escape(name) + r'\b'
            result = re.sub(pattern, str(value), result)
            
        return result
        
    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate a condition string"""
        if not condition:
            return True
            
        # Expand variables in the condition
        expanded_condition = self.expand_variables(condition)
        
        # Common condition shorthands
        if expanded_condition == "success":
            # Previous step succeeded
            if len(self.steps) < 2:
                return True
            prev_step = self.steps[-2]
            return prev_step.status == "success"
            
        if expanded_condition == "error":
            # Previous step failed
            if len(self.steps) < 2:
                return False
            prev_step = self.steps[-2]
            return prev_step.status == "error"
            
        if expanded_condition.startswith("exit_code "):
            # Check specific exit code
            if len(self.steps) < 2:
                return False
            prev_step = self.steps[-2]
            if not prev_step.result:
                return False
                
            parts = expanded_condition.split()
            if len(parts) != 3:
                return False
                
            _, op, value = parts
            exit_code = prev_step.result.get("exit_code", -1)
            
            if op == "==":
                return exit_code == int(value)
            elif op == "!=":
                return exit_code != int(value)
            elif op == "<":
                return exit_code < int(value)
            elif op == ">":
                return exit_code > int(value)
            elif op == "<=":
                return exit_code <= int(value)
            elif op == ">=":
                return exit_code >= int(value)
                
        # Default to True if condition can't be evaluated
        return True
        
    def execute(self, fail_fast: bool = True) -> Dict[str, Any]:
        """Execute the command chain"""
        results = []
        any_errors = False
        
        for i, step in enumerate(self.steps):
            # Check if step should be executed based on condition
            should_execute = self.evaluate_condition(step.condition)
            
            if not should_execute:
                step.status = "skipped"
                step.result = {"exit_code": None, "stdout": "", "stderr": "Step skipped due to condition"}
                results.append(step.to_dict())
                
                # Call step complete callback
                if self.on_step_complete:
                    self.on_step_complete(step, i, len(self.steps))
                    
                continue
                
            # Prepare to execute the step
            step.status = "running"
            step.start_time = time.time()
            
            # Call step start callback
            if self.on_step_start:
                self.on_step_start(step, i, len(self.steps))
                
            # Expand variables in the command
            expanded_command = self.expand_variables(step.command)
            
            # Execute the command
            result = self._execute_command(expanded_command, step)
            step.result = result
            step.end_time = time.time()
            
            # Update step status
            if result["exit_code"] == 0:
                step.status = "success"
            else:
                step.status = "error"
                any_errors = True
                
            # Store command output in variables if format is like "var=$(command)"
            self._extract_output_variables(step)
            
            # Call step complete callback
            if self.on_step_complete:
                self.on_step_complete(step, i, len(self.steps))
                
            results.append(step.to_dict())
            
            # Check if execution should stop on error
            if fail_fast and step.status == "error":
                break
                
        # Call chain complete callback
        if self.on_chain_complete:
            self.on_chain_complete(self.steps, any_errors)
            
        return {
            "name": self.name,
            "steps": results,
            "success": not any_errors,
            "working_dir": self.working_dir,
            "steps_total": len(self.steps),
            "steps_executed": len([s for s in self.steps if s.status != "pending"]),
            "steps_successful": len([s for s in self.steps if s.status == "success"]),
            "steps_failed": len([s for s in self.steps if s.status == "error"]),
            "steps_skipped": len([s for s in self.steps if s.status == "skipped"])
        }
        
    def _execute_command(self, command: str, step: CommandStep) -> Dict[str, Any]:
        """Execute a single command"""
        cwd = step.cwd or self.working_dir
        
        try:
            process = subprocess.Popen(
                command,
                shell=step.shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd
            )
            
            try:
                stdout, stderr = process.communicate(timeout=step.timeout)
                return {
                    "exit_code": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "command": command,
                    "execution_time": time.time() - step.start_time
                }
            except subprocess.TimeoutExpired:
                process.kill()
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Command timed out after {step.timeout} seconds",
                    "command": command,
                    "execution_time": step.timeout
                }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "command": command,
                "execution_time": time.time() - step.start_time
            }
            
    def _extract_output_variables(self, step: CommandStep) -> None:
        """Extract output from command into variables based on naming pattern"""
        # Look for patterns like "VAR=$(command)" in the original command
        pattern = r'(\w+)=\$\((.*?)\)'
        matches = re.findall(pattern, step.command)
        
        for var_name, cmd in matches:
            # If command succeeded, store its output as a variable
            if step.status == "success" and step.result:
                output = step.result.get("stdout", "").strip()
                self.variables[var_name] = output
                
    def to_dict(self) -> Dict[str, Any]:
        """Convert chain to a dictionary for serialization"""
        return {
            "name": self.name,
            "working_dir": self.working_dir,
            "steps": [step.to_dict() for step in self.steps],
            "variables": self.variables
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandChain':
        """Create a chain from a dictionary"""
        chain = cls(
            name=data.get("name"),
            working_dir=data.get("working_dir")
        )
        
        # Restore variables
        for name, value in data.get("variables", {}).items():
            chain.set_variable(name, value)
            
        # Restore steps
        for step_data in data.get("steps", []):
            step = CommandStep.from_dict(step_data)
            chain.steps.append(step)
            
        return chain
    
    def get_result_summary(self) -> str:
        """Get a summary of execution results"""
        result = []
        result.append(f"Command Chain: {self.name}")
        result.append(f"Working Directory: {self.working_dir}")
        result.append(f"Steps: {len(self.steps)}")
        
        success_count = len([s for s in self.steps if s.status == "success"])
        error_count = len([s for s in self.steps if s.status == "error"])
        skipped_count = len([s for s in self.steps if s.status == "skipped"])
        pending_count = len([s for s in self.steps if s.status == "pending"])
        
        result.append(f"Results: {success_count} succeeded, {error_count} failed, {skipped_count} skipped, {pending_count} pending")
        
        for i, step in enumerate(self.steps):
            status_icon = {
                "success": "✓", 
                "error": "✗", 
                "skipped": "⨯",
                "pending": "○",
                "running": "▶"
            }.get(step.status, "?")
            
            result.append(f"\n{i+1}. [{status_icon}] {step.name}")
            result.append(f"   Command: {step.command}")
            
            if step.condition:
                result.append(f"   Condition: {step.condition}")
                
            if step.status != "pending":
                if step.result:
                    exit_code = step.result.get("exit_code")
                    execution_time = step.result.get("execution_time", 0)
                    result.append(f"   Exit Code: {exit_code}")
                    result.append(f"   Time: {execution_time:.2f}s")
                    
                    # Include output for errors
                    if step.status == "error":
                        stderr = step.result.get("stderr", "").strip()
                        if stderr:
                            result.append(f"   Error: {stderr[:200]}")
                            if len(stderr) > 200:
                                result.append("   ...")
                                
        return "\n".join(result)

    @classmethod
    def get_all_chains(cls) -> Dict[str, 'CommandChain']:
        """Get all registered command chains"""
        return cls._chains
    
    @classmethod
    def get_chain(cls, name: str) -> Optional['CommandChain']:
        """Get a specific command chain by name"""
        return cls._chains.get(name)
    
    @classmethod
    def delete_chain(cls, name: str) -> bool:
        """Delete a command chain by name"""
        if name in cls._chains:
            del cls._chains[name]
            return True
        return False 