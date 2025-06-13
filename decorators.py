"""
Decorator utilities for code analysis
"""

def analyze_source_decorators(source_lines):
    """Analyze Python decorators in source code"""
    decorators = []
    for line in source_lines:
        line = line.strip()
        if line.startswith('@'):
            decorators.append(line[1:].split('(')[0])
    return decorators

def count_decorators(decorators):
    """Count decorator occurrences"""
    counts = {}
    for decorator in decorators:
        counts[decorator] = counts.get(decorator, 0) + 1
    return counts

def parse_decorator_args(decorator_line):
    """Parse decorator arguments"""
    if '(' not in decorator_line:
        return None
    args_str = decorator_line.split('(', 1)[1].rsplit(')', 1)[0]
    return [arg.strip() for arg in args_str.split(',') if arg.strip()]