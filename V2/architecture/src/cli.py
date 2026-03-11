"""
Command Line Interface for Kiro Agent System
"""

import asyncio
import sys
import yaml
from pathlib import Path
from typing import Optional

from core.orchestrator import CoreOrchestrator
from models.agent import UserRequest
from utils.logger import setup_logger
from utils.config import load_config


class CLI:
    """Command line interface"""
    
    def __init__(self):
        self.orchestrator: Optional[CoreOrchestrator] = None
        self.logger = setup_logger(__name__)
        self.config = None
        self.session_id = "cli-session"
        self.user_id = "cli-user"
    
    async def run(self):
        """Run CLI"""
        
        # Load configuration
        self.config = load_config()
        
        # Initialize orchestrator
        self.orchestrator = CoreOrchestrator(self.config)
        await self.orchestrator.initialize()
        
        self.logger.info("Kiro Agent System initialized")
        
        # Check if command provided
        if len(sys.argv) > 1:
            # Single command mode
            command = ' '.join(sys.argv[1:])
            await self.process_command(command)
        else:
            # Interactive mode
            await self.interactive_mode()
        
        # Shutdown
        await self.orchestrator.shutdown()
    
    async def interactive_mode(self):
        """Interactive mode"""
        
        print("=" * 60)
        print("Kiro Agent System - Interactive Mode")
        print("=" * 60)
        print("\nCommands:")
        print("  - Type your request naturally")
        print("  - 'help' - Show help")
        print("  - 'exit' or 'quit' - Exit")
        print("=" * 60)
        print()
        
        while True:
            try:
                # Get user input
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye!")
                    break
                
                # Check for help
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                # Process command
                await self.process_command(user_input)
                
            except KeyboardInterrupt:
                print("\n\nUse 'exit' to quit")
                continue
            except Exception as e:
                self.logger.error(f"Error: {e}", exc_info=True)
                print(f"\nError: {e}")
    
    async def process_command(self, command: str):
        """Process a command"""
        
        print(f"\nProcessing: {command}")
        print("-" * 60)
        
        # Create user request
        request = UserRequest(
            text=command,
            user_id=self.user_id,
            session_id=self.session_id
        )
        
        try:
            # Process request
            result = await self.orchestrator.process_request(request)
            
            # Display result
            self.display_result(result)
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}", exc_info=True)
            print(f"\nError: {e}")
    
    def display_result(self, result):
        """Display result"""
        
        print(f"\nStatus: {result.status}")
        
        if result.output:
            print(f"\nOutput:\n{result.output}")
        
        if result.files_created:
            print(f"\nFiles created:")
            for file in result.files_created:
                print(f"  - {file}")
        
        if result.files_modified:
            print(f"\nFiles modified:")
            for file in result.files_modified:
                print(f"  - {file}")
        
        if result.error:
            print(f"\nError: {result.error}")
        
        print("-" * 60)
    
    def show_help(self):
        """Show help"""
        
        print("\n" + "=" * 60)
        print("Kiro Agent System - Help")
        print("=" * 60)
        print("\nAvailable Commands:")
        print("\n1. Create Feature Spec:")
        print("   > Add user authentication")
        print("   > Create a dashboard component")
        print("\n2. Fix Bug:")
        print("   > Fix crash when quantity is zero")
        print("   > App doesn't load on mobile")
        print("\n3. Execute Task:")
        print("   > Execute task 2 from user-auth spec")
        print("   > Run all tasks from dashboard spec")
        print("\n4. General Tasks:")
        print("   > Refactor the UserList component")
        print("   > Add tests for authentication")
        print("\n5. Analysis:")
        print("   > How is authentication implemented?")
        print("   > Where is the login logic?")
        print("\n6. System Commands:")
        print("   > help - Show this help")
        print("   > exit - Exit the system")
        print("=" * 60)


def main():
    """Main function"""
    cli = CLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
