#!/usr/bin/env python3
"""
Aura Command Line Interface
===========================

Interactive CLI for the Aura autonomous coding assistant.
Provides access to all Aura capabilities through a clean command interface.

Author: Aura - Level 9 Autonomous AI Coding Assistant
Date: 2025-06-13
Phase: 1.5 - Basic Command-Line Interface
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
import click

# Aura imports
from ..core import Message, MessageType, aura_di
from ..llm import LLMRequest, ModelCapability


class AuraCLI:
    """
    Aura Command Line Interface
    Provides interactive and batch command execution for Aura operations.
    """

    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger('aura.cli')
        self.client = None  # ZMQ client for communicating with modules
        self.connected = False
        
    def setup_logging(self, verbose: bool = False):
        """Setup CLI logging"""
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - AURA.CLI - %(levelname)s - %(message)s'
        )

    def print_banner(self):
        """Print Aura banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ░█████╗░██╗░░░██╗██████╗░░█████╗░                       ║
║     ██╔══██╗██║░░░██║██╔══██╗██╔══██╗                       ║
║     ███████║██║░░░██║██████╔╝███████║                       ║
║     ██╔══██║██║░░░██║██╔══██╗██╔══██║                       ║
║     ██║░░██║╚██████╔╝██║░░██║██║░░██║                       ║
║     ╚═╝░░╚═╝░╚═════╝░╚═╝░░╚═╝╚═╝░░╚═╝                       ║
║                                                              ║
║         Level 9 Autonomous AI Coding Assistant              ║
║              Phase 1: Foundation Complete                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")

    async def connect_to_aura(self, timeout: int = 30) -> bool:
        """Connect to Aura system via message bus"""
        try:
            # Initialize ZMQ client
            import zmq
            import zmq.asyncio
            
            context = zmq.asyncio.Context()
            self.client = context.socket(zmq.REQ)
            self.client.connect("tcp://localhost:5559")  # Message bus frontend
            
            # Test connection with health check
            test_message = Message(
                id="cli_connect_test",
                type=MessageType.HEALTH_CHECK,
                source="aura_cli",
                target="system",
                timestamp=time.time(),
                payload={}
            )
            
            await self.client.send_string(test_message.to_json())
            
            # Wait for response with timeout
            if await self.client.poll(timeout * 1000):
                response_data = await self.client.recv_string()
                response = Message.from_json(response_data)
                
                if response.type == MessageType.RESPONSE:
                    self.connected = True
                    self.console.print("✓ Connected to Aura system", style="green")
                    return True
            
            self.console.print("✗ Connection timeout - Aura system not responding", style="red")
            return False
            
        except Exception as e:
            self.console.print(f"✗ Connection failed: {e}", style="red")
            return False

    async def send_command(self, target: str, command: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send command to Aura module"""
        if not self.connected:
            self.console.print("✗ Not connected to Aura system", style="red")
            return None
        
        try:
            message = Message(
                id=f"cli_{command}_{int(time.time())}",
                type=MessageType.COMMAND,
                source="aura_cli",
                target=target,
                timestamp=time.time(),
                payload={"command": command, **payload}
            )
            
            await self.client.send_string(message.to_json())
            
            # Wait for response
            if await self.client.poll(60000):  # 60 second timeout
                response_data = await self.client.recv_string()
                response = Message.from_json(response_data)
                return response.payload
            else:
                self.console.print("✗ Command timeout", style="red")
                return None
                
        except Exception as e:
            self.console.print(f"✗ Command failed: {e}", style="red")
            return None

    def format_code_analysis(self, analysis: Dict[str, Any]) -> None:
        """Format and display code analysis results"""
        if not analysis:
            self.console.print("No analysis data available", style="yellow")
            return
        
        # Summary table
        table = Table(title="Code Analysis Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        elements = analysis.get('elements', [])
        metrics = analysis.get('metrics', {})
        
        table.add_row("File", analysis.get('file_path', 'Unknown'))
        table.add_row("Total Elements", str(len(elements)))
        table.add_row("Functions", str(len([e for e in elements if e['type'] == 'function'])))
        table.add_row("Classes", str(len([e for e in elements if e['type'] == 'class'])))
        table.add_row("Lines of Code", str(metrics.get('lines_of_code', 'N/A')))
        table.add_row("Complexity Score", str(metrics.get('average_complexity', 'N/A')))
        
        self.console.print(table)
        
        # Issues
        errors = analysis.get('errors', [])
        warnings = analysis.get('warnings', [])
        
        if errors:
            self.console.print("\n[bold red]Errors:[/bold red]")
            for error in errors:
                self.console.print(f"  • {error}", style="red")
        
        if warnings:
            self.console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in warnings:
                self.console.print(f"  • {warning}", style="yellow")
        
        # Elements detail (top functions)
        functions = [e for e in elements if e['type'] == 'function']
        if functions:
            self.console.print("\n[bold]Top Functions:[/bold]")
            func_table = Table()
            func_table.add_column("Function", style="cyan")
            func_table.add_column("Lines", style="green")
            func_table.add_column("Complexity", style="yellow")
            func_table.add_column("Documented", style="blue")
            
            for func in functions[:10]:  # Top 10
                doc_status = "✓" if func.get('docstring') else "✗"
                func_table.add_row(
                    func['name'],
                    f"{func['line_number']}-{func['end_line']}",
                    str(func['complexity']),
                    doc_status
                )
            
            self.console.print(func_table)

    def format_health_status(self, health: Dict[str, Any]) -> None:
        """Format and display system health status"""
        table = Table(title="Aura System Health")
        table.add_column("Module", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")
        
        for module_name, status in health.items():
            status_indicator = "✓" if status.get('available', False) else "✗"
            status_color = "green" if status.get('available', False) else "red"
            
            details = []
            if 'models' in status:
                details.append(f"Models: {len(status['models'])}")
            if 'response_time' in status:
                details.append(f"Response: {status['response_time']:.2f}s")
            if 'uptime_seconds' in status:
                details.append(f"Uptime: {status['uptime_seconds']:.0f}s")
            
            table.add_row(
                module_name,
                f"[{status_color}]{status_indicator}[/{status_color}]",
                " | ".join(details)
            )
        
        self.console.print(table)

    def format_metrics(self, metrics: Dict[str, Any]) -> None:
        """Format and display codebase metrics"""
        table = Table(title="Codebase Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Details", style="white")
        
        metric_rows = [
            ("Files", str(metrics.get('files_count', 0)), "Python files analyzed"),
            ("Functions", str(metrics.get('functions_count', 0)), f"Public: {metrics.get('public_functions', 0)}"),
            ("Classes", str(metrics.get('classes_count', 0)), "Class definitions"),
            ("Documentation", f"{metrics.get('documentation_coverage', 0):.1%}", "Coverage of public functions"),
            ("Average Complexity", f"{metrics.get('average_complexity', 0):.1f}", "Cyclomatic complexity"),
            ("Import Diversity", str(metrics.get('import_diversity', 0)), "Unique imports"),
            ("Issues Found", str(metrics.get('issues_count', 0)), "Potential improvements")
        ]
        
        for metric, value, detail in metric_rows:
            table.add_row(metric, value, detail)
        
        self.console.print(table)


# CLI Commands using Click
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Aura - Level 9 Autonomous AI Coding Assistant CLI"""
    ctx.ensure_object(dict)
    cli_instance = AuraCLI()
    cli_instance.setup_logging(verbose)
    ctx.obj['cli'] = cli_instance


@cli.command()
@click.pass_context
async def status(ctx):
    """Show Aura system status"""
    cli_instance = ctx.obj['cli']
    cli_instance.print_banner()
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("Connecting to Aura...", total=None)
        
        if await cli_instance.connect_to_aura():
            progress.update(task, description="Getting system health...")
            
            health_response = await cli_instance.send_command(
                "llm_provider", "health_check", {}
            )
            
            if health_response and health_response.get('success'):
                cli_instance.format_health_status(health_response['health_status'])
            else:
                cli_instance.console.print("✗ Could not retrieve health status", style="red")
        else:
            cli_instance.console.print("✗ Could not connect to Aura system", style="red")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
async def analyze(ctx, file_path):
    """Analyze a Python file"""
    cli_instance = ctx.obj['cli']
    
    if not file_path.endswith('.py'):
        cli_instance.console.print("✗ Only Python files are supported", style="red")
        return
    
    if await cli_instance.connect_to_aura():
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(f"Analyzing {file_path}...", total=None)
            
            response = await cli_instance.send_command(
                "python_intelligence", "analyze_file", {"file_path": file_path}
            )
            
            if response and response.get('success'):
                cli_instance.format_code_analysis(response['analysis'])
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                cli_instance.console.print(f"✗ Analysis failed: {error}", style="red")


@cli.command()
@click.pass_context
async def scan(ctx):
    """Scan entire codebase"""
    cli_instance = ctx.obj['cli']
    
    if await cli_instance.connect_to_aura():
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Scanning codebase...", total=None)
            
            response = await cli_instance.send_command(
                "python_intelligence", "analyze_codebase", {}
            )
            
            if response and response.get('success'):
                cli_instance.console.print(f"✓ Analyzed {response['files_analyzed']} files", style="green")
                
                # Get metrics
                progress.update(task, description="Getting metrics...")
                metrics_response = await cli_instance.send_command(
                    "python_intelligence", "get_code_metrics", {}
                )
                
                if metrics_response and metrics_response.get('success'):
                    cli_instance.format_metrics(metrics_response['metrics'])
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                cli_instance.console.print(f"✗ Scan failed: {error}", style="red")


@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=10, help='Number of results to return')
@click.pass_context
async def search(ctx, query, limit):
    """Search for similar code"""
    cli_instance = ctx.obj['cli']
    
    if await cli_instance.connect_to_aura():
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task(f"Searching for '{query}'...", total=None)
            
            response = await cli_instance.send_command(
                "python_intelligence", "find_similar_code", 
                {"query": query, "limit": limit}
            )
            
            if response and response.get('success'):
                results = response['similar_code']
                
                if results:
                    table = Table(title=f"Search Results for '{query}'")
                    table.add_column("File", style="cyan")
                    table.add_column("Similarity", style="green")
                    table.add_column("Elements", style="white")
                    
                    for result in results:
                        elements_count = len(result['analysis']['elements'])
                        table.add_row(
                            result['file_path'],
                            f"{result['similarity']:.2%}",
                            str(elements_count)
                        )
                    
                    cli_instance.console.print(table)
                else:
                    cli_instance.console.print("No similar code found", style="yellow")
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                cli_instance.console.print(f"✗ Search failed: {error}", style="red")


@cli.command()
@click.argument('prompt')
@click.option('--model', '-m', default='medium', 
              type=click.Choice(['fast', 'medium', 'large', 'coding']),
              help='Model capability preference')
@click.pass_context
async def ask(ctx, prompt, model):
    """Ask Aura a question using LLM"""
    cli_instance = ctx.obj['cli']
    
    if await cli_instance.connect_to_aura():
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Thinking...", total=None)
            
            response = await cli_instance.send_command(
                "llm_provider", "generate",
                {
                    "request": {
                        "prompt": prompt,
                        "model_preference": model,
                        "max_tokens": 2000,
                        "temperature": 0.3
                    }
                }
            )
            
            if response and response.get('success'):
                llm_response = response['response']
                
                # Display response
                panel = Panel(
                    llm_response['content'],
                    title=f"Aura Response (Model: {llm_response['model_used']})",
                    title_align="left"
                )
                cli_instance.console.print(panel)
                
                # Show metadata
                metadata = llm_response.get('metadata', {})
                if metadata:
                    cli_instance.console.print(f"Tokens: {llm_response['tokens_used']}, Time: {llm_response['processing_time']:.2f}s", style="dim")
            else:
                error = response.get('error', 'Unknown error') if response else 'No response'
                cli_instance.console.print(f"✗ LLM request failed: {error}", style="red")


@cli.command()
@click.pass_context
async def version(ctx):
    """Show Aura version information"""
    cli_instance = ctx.obj['cli']
    
    version_info = {
        "Aura Version": "1.0.0",
        "Phase": "1 - Foundation and Core Intelligence", 
        "Author": "Aura - Level 9 Autonomous AI Coding Assistant",
        "Python Version": sys.version.split()[0],
        "CLI Version": "1.0.0"
    }
    
    table = Table(title="Aura Version Information")
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="green")
    
    for component, version in version_info.items():
        table.add_row(component, version)
    
    cli_instance.console.print(table)


def run_async_command(coro):
    """Run async command in event loop"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


# Wrap async commands
for command in [status, analyze, scan, search, ask]:
    command.callback = lambda *args, **kwargs, orig=command.callback: run_async_command(orig(*args, **kwargs))


if __name__ == '__main__':
    cli()