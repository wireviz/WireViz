#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import wireviz.wireviz as wv

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
"""Wireviz Kroki wrapper.
Reads YAML data from stdin and writes output to stdout.
Errors and messages from WireViz are printed to stderr.""")   
    
    output_formats = ["svg", "png", "harness"]

    parser.add_argument("--format", type=str, required=True, choices=output_formats, 
                        help=f"Supported output formats.")
    parser.add_argument("output", type=str, choices=["-"], help="'-' for stdout")
    args = parser.parse_args()
    
    try:
        data = wv.parse(inp = sys.stdin.read(), return_types=args.format)
        if not args.output == "-":
            raise ValueError("Only stdout output is supported")

        if isinstance(data, str):
            sys.stdout.write(data)
        elif isinstance(data, bytes):
            sys.stdout.buffer.write(data)
        else:
            raise ValueError("Unsupported data format")

    except Exception as e:
        sys.stderr.write(str(e))