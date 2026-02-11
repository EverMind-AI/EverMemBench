"""
Supermemory Adapter for multi-person group chat evaluation.

Implements Add functionality for Supermemory memory system.
All messages are sent with timestamp prefix (API doesn't support metadata timestamp):
[2025-01-09T09:32:15][Group: X][Speaker: Name]content
"""
import asyncio
from datetime import timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from eval.src.adapters.base import BaseAdapter
from eval.src.core.data_models import Dataset, GroupChatDay, GroupChatMessage, AddResult
from eval.src.utils.logger import get_console, print_success, print_error, print_warning


class SupermemoryAdapter(BaseAdapter):
    """
    Supermemory memory system adapter for multi-person group chat.
    
    Formats all messages with TIMESTAMP PREFIX (API doesn't support metadata timestamp):
    - content: "[2025-01-09T09:32:15][Group: X][Speaker: Name]original_content"
    - container_tag: user_id
    
    Config example:
    ```yaml
    name: "supermemory"
    api_key: "${SUPERMEMORY_API_KEY}"
    batch_size: 20
    ```
    """
    
    def __init__(self, config: Dict[str, Any], output_dir: Optional[Path] = None):
        super().__init__(config, output_dir)
        
        # Import Supermemory client
        try:
            from supermemory import Supermemory
        except ImportError:
            raise ImportError(
                "Supermemory client not installed. "
                "Please install: pip install supermemory"
            )
        
        # API configuration
        api_key = config.get("api_key", "")
        if not api_key:
            raise ValueError("Supermemory API key is required. Set 'api_key' in config or SUPERMEMORY_API_KEY env var.")
        
        self.client = Supermemory(api_key=api_key)
        
        # Batch configuration
        self.batch_size = config.get("batch_size", 20)
        self.max_retries = config.get("max_retries", 5)
        
        self.console = get_console()
        
        print(f"✅ SupermemoryAdapter initialized")
        print(f"   Batch Size: {self.batch_size}")
    
    async def add(
        self,
        dataset: Dataset,
        user_id: str,
        days_to_process: Optional[List[str]] = None,
        **kwargs
    ) -> AddResult:
        """
        Add dataset to Supermemory memory system.
        
        Args:
            dataset: Dataset with group chat data
            user_id: User ID (container_tag) for Supermemory
            days_to_process: Optional list of dates to process (None = all)
            **kwargs: Additional parameters
            
        Returns:
            AddResult with statistics
        """
        self.console.print(f"\n{'='*60}", style="bold cyan")
        self.console.print("Stage: Add (Supermemory)", style="bold cyan")
        self.console.print(f"{'='*60}", style="bold cyan")
        self.console.print(f"User ID (container_tag): {user_id}")
        self.console.print(f"Dataset: {dataset.name}")
        
        # Determine which days to process
        if days_to_process:
            days = [d for d in dataset.days if d.date in days_to_process]
        else:
            days = dataset.days
        
        self.console.print(f"Days to process: {len(days)}")
        
        total_messages = 0
        total_errors = []
        
        # Process each day
        for day in days:
            self.console.print(f"\n📅 Processing {day.date}...", style="dim")

            # Process each group separately to avoid cross-group batching
            for group_name, messages in day.groups.items():
                self.console.print(f"   👥 Group: {group_name}", style="dim")

                group_messages = [self._format_message(m) for m in messages]
                self.console.print(f"      Messages: {len(group_messages)}")

                batches = self._split_into_batches(group_messages)
                self.console.print(f"      Batches: {len(batches)}")

                for batch_idx, batch in enumerate(batches):
                    try:
                        # Include group_name in conv_id metadata for traceability
                        await self._send_batch(batch, user_id, f"{day.date}_{group_name}", batch_idx)
                        total_messages += len(batch)
                        self.console.print(
                            f"      ✅ Batch {batch_idx + 1}/{len(batches)} sent ({len(batch)} messages)",
                            style="dim green",
                        )
                    except Exception as e:
                        error_msg = f"[{day.date}][{group_name}] Batch {batch_idx + 1} failed: {e}"
                        total_errors.append(error_msg)
                        self.console.print(f"      ❌ {error_msg}", style="red")
        
        # Summary
        success = len(total_errors) == 0
        
        self.console.print(f"\n{'='*60}", style="bold cyan")
        if success:
            print_success(f"Add completed: {total_messages} messages sent")
        else:
            print_warning(f"Add completed with errors: {total_messages} messages, {len(total_errors)} errors")
        
        return AddResult(
            success=success,
            days_processed=len(days),
            messages_sent=total_messages,
            errors=total_errors,
            metadata={
                "user_id": user_id,
                "dataset": dataset.name,
            }
        )
    
    def _format_message(self, msg: GroupChatMessage) -> str:
        """
        Format a GroupChatMessage for Supermemory API.
        
        IMPORTANT: Timestamp is included as PREFIX because Supermemory API
        doesn't support metadata timestamp.
        
        Input: GroupChatMessage with speaker, content, timestamp, group
        Output: "[2025-01-09T09:32:15][Group: X][Speaker: Name]content"
        """
        # Format timestamp
        ts = msg.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        timestamp_str = ts.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Format content with timestamp, group and speaker prefix
        formatted_content = f"[{timestamp_str}][Group: {msg.group}][Speaker: {msg.speaker}]{msg.content}"
        
        return formatted_content
    
    def _split_into_batches(self, messages: List[str]) -> List[List[str]]:
        """
        Split messages into batches.
        
        Args:
            messages: List of formatted message strings
            
        Returns:
            List of batches
        """
        batches = []
        for i in range(0, len(messages), self.batch_size):
            batches.append(messages[i:i + self.batch_size])
        return batches
    
    async def _send_batch(self, messages: List[str], user_id: str, date: str, batch_idx: int):
        """
        Send a batch of messages to Supermemory API.
        
        Supermemory expects a single content string, so we join messages with newlines.
        
        Args:
            messages: List of formatted message strings
            user_id: Container tag for Supermemory
            date: Date string for metadata
            batch_idx: Batch index for conversation ID
            
        Raises:
            Exception: If API call fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                # Join messages into a single content string
                content = "\n".join(messages)
                
                # Run synchronous Supermemory operations in executor
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self._sync_add_memory,
                    content,
                    user_id,
                    f"{date}_batch{batch_idx}"
                )
                return  # Success
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    self.console.print(
                        f"      ⚠️  Retry {attempt + 1}/{self.max_retries} in {wait_time}s: {e}",
                        style="yellow"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise
    
    def _sync_add_memory(self, content: str, user_id: str, conv_id: str):
        """
        Synchronous memory add for Supermemory.
        
        Args:
            content: Formatted content string with all messages
            user_id: Container tag
            conv_id: Conversation ID for metadata
        """
        self.client.memories.add(
            content=content,
            container_tag=user_id,
            metadata={
                "conv_id": conv_id
            }
        )
    
    async def close(self):
        """Close client resources."""
        pass  # Supermemory client doesn't require explicit cleanup

