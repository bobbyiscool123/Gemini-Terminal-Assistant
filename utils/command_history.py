"""
Command History Management Module
Provides enhanced command history functionality with search, browsing, and persistence.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Callable

class CommandHistory:
    def __init__(self, history_file: str = "command_history.json", max_entries: int = 1000):
        self.history_file = history_file
        self.max_entries = max_entries
        self.history: List[Dict] = []
        self.position = -1  # Current position in history when browsing
        self.search_results: List[int] = []  # Indices of search results
        self.search_position = -1  # Position in search results
        self.on_history_change: Optional[Callable] = None
        
        self.load()
    
    def add(self, entry: Dict) -> None:
        """Add a command entry to history"""
        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()
            
        # Add to history
        self.history.append(entry)
        
        # Trim history if needed
        if len(self.history) > self.max_entries:
            self.history = self.history[-self.max_entries:]
            
        # Notify listeners
        if self.on_history_change:
            self.on_history_change(self.history)
    
    def save(self) -> None:
        """Save history to file"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def load(self) -> None:
        """Load history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except json.JSONDecodeError:
                self.history = []
    
    def clear(self) -> None:
        """Clear command history"""
        self.history = []
        self.position = -1
        self.search_results = []
        self.search_position = -1
        
        # Notify listeners
        if self.on_history_change:
            self.on_history_change(self.history)
    
    def get_previous(self) -> Optional[Dict]:
        """Get previous command in history"""
        if not self.history:
            return None
            
        if self.position < len(self.history) - 1:
            self.position += 1
            return self.history[-(self.position + 1)]
        return self.history[0]
    
    def get_next(self) -> Optional[Dict]:
        """Get next command in history"""
        if not self.history or self.position <= 0:
            self.position = -1
            return None
            
        self.position -= 1
        if self.position == -1:
            return None
        return self.history[-(self.position + 1)]
    
    def reset_position(self) -> None:
        """Reset browsing position"""
        self.position = -1
    
    def search(self, query: str) -> List[Dict]:
        """Search history for commands containing query"""
        self.search_results = []
        self.search_position = -1
        
        if not query:
            return []
            
        query = query.lower()
        results = []
        
        for i, entry in enumerate(self.history):
            command = entry.get("command", "").lower()
            if query in command:
                self.search_results.append(i)
                results.append(entry)
                
        return results
    
    def get_next_search_result(self) -> Optional[Dict]:
        """Get next search result"""
        if not self.search_results:
            return None
            
        if self.search_position < len(self.search_results) - 1:
            self.search_position += 1
            index = self.search_results[self.search_position]
            return self.history[index]
        return None
    
    def get_previous_search_result(self) -> Optional[Dict]:
        """Get previous search result"""
        if not self.search_results or self.search_position <= 0:
            return None
            
        self.search_position -= 1
        index = self.search_results[self.search_position]
        return self.history[index]
    
    def get_by_index(self, index: int) -> Optional[Dict]:
        """Get history entry by index"""
        if 0 <= index < len(self.history):
            return self.history[index]
        return None
    
    def get_last_n(self, n: int) -> List[Dict]:
        """Get last n history entries"""
        return self.history[-n:] if self.history else []
    
    def get_stats(self) -> Dict:
        """Get history statistics"""
        if not self.history:
            return {
                "count": 0,
                "success_rate": 0,
                "most_common": None,
                "avg_execution_time": 0
            }
            
        # Calculate stats
        count = len(self.history)
        
        # Success rate
        successes = sum(1 for entry in self.history if entry.get("exit_code", 1) == 0)
        success_rate = (successes / count) * 100 if count > 0 else 0
        
        # Most common command
        command_counts = {}
        for entry in self.history:
            cmd = entry.get("command", "")
            command_counts[cmd] = command_counts.get(cmd, 0) + 1
        
        most_common = max(command_counts.items(), key=lambda x: x[1]) if command_counts else (None, 0)
        
        # Average execution time
        times = [entry.get("execution_time", 0) for entry in self.history]
        avg_time = sum(times) / len(times) if times else 0
        
        return {
            "count": count,
            "success_rate": success_rate,
            "most_common": most_common[0],
            "most_common_count": most_common[1],
            "avg_execution_time": avg_time
        } 