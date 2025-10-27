#!/usr/bin/env python3
"""
passwordchecker.py
Password Strength Analyzer + Custom Wordlist Generator

Usage:
  CLI: python passwordchecker.py --password "P@ssw0rd123" --inputs Vijay 2000 Tiger
  Interactive: python passwordchecker.py
"""

import argparse
import itertools
import os
import sys
from typing import List, Set

# Try imports and give helpful message if missing
try:
    from zxcvbn import zxcvbn
except Exception as e:
    print("Missing dependency: zxcvbn. Install with: pip install zxcvbn")
    raise

# ---- Leetspeak mapping (small, useful set) ----
LEET_MAP = {
    'a': ['a', '@', '4'],
    'b': ['b', '8'],
    'e': ['e', '3'],
    'i': ['i', '1', '!'],
    'l': ['l', '1'],
    'o': ['o', '0'],
    's': ['s', '$', '5'],
    't': ['t', '7'],
    'g': ['g', '9'],
    # letters not listed will just map to themselves
}

# limiters to keep output sizes reasonable
MAX_LEET_COMBINATIONS = 5000  # don't generate more than this many leet variants per base word
MAX_FINAL_WORDLIST_SIZE = 200000  # safety cap for final output


def analyze_password(password: str) -> dict:
    """Run zxcvbn analysis and return the result dict."""
    if not password:
        raise ValueError("Password is empty.")
    result = zxcvbn(password)
    # nice printout
    print("\n--- Password Strength Analysis ---")
    print(f"Password (analyzed): {password}")
    print(f"Score: {result.get('score')} / 4")
    print(f"Estimated guesses: {result.get('guesses')}")
    crack_times = result.get('crack_times_display', {})
    print("Crack time estimates (display):")
    for k, v in crack_times.items():
        print(f"  {k}: {v}")
    feedback = result.get('feedback', {})
    if feedback:
        print("Feedback:")
        if feedback.get('warning'):
            print(f"  Warning: {feedback['warning']}")
        if feedback.get('suggestions'):
            for s in feedback['suggestions']:
                print(f"  - {s}")
    print("----------------------------------\n")
    return result


def case_variations(word: str) -> List[str]:
    """Return a small set of case variations to include."""
    variants = set()
    variants.add(word)
    variants.add(word.lower())
    variants.add(word.upper())
    # capitalized only if not already proper case
    variants.add(word.capitalize())
    return sorted(variants)


def generate_leet_variants(word: str, cap: int = MAX_LEET_COMBINATIONS) -> Set[str]:
    """
    Generate leet variants for a word but cap the number returned.
    We build combos from the LEET_MAP but stop early if the product explodes.
    """
    if not word:
        return set()

    # Build list of possible characters for each position
    choices = []
    for ch in word:
        lower = ch.lower()
        if lower in LEET_MAP:
            # keep both same-case and leet options
            options = list(dict.fromkeys([ch] + LEET_MAP[lower]))  # preserve order, dedupe
        else:
            options = [ch]
        choices.append(options)

    # compute estimated size and bail if too large
    estimated = 1
    for c in choices:
        estimated *= len(c)
        if estimated > cap * 5:  # soft check before iterating
            break

    variants = set()
    # Use product but stop when cap reached
    for combo in itertools.product(*choices):
        variants.add(''.join(combo))
        if len(variants) >= cap:
            break
    return variants


def build_base_words(inputs: List[str]) -> List[str]:
    """Create a base set of words from inputs (and some common affixes)."""
    affixes = ['', '123', '!', '@', '2025', '01', '07']
    base = set()
    for inp in inputs:
        inp = str(inp).strip()
        if not inp:
            continue
        # add raw and simple transforms
        for v in case_variations(inp):
            base.add(v)
            # attach affixes to each case variation
            for aff in affixes:
                base.add(v + aff)
    # create simple concatenations: all pairwise combos (limited)
    inputs_lower = [x.lower() for x in inputs if x]
    for a in inputs_lower:
        for b in inputs_lower:
            if a != b and len(a) + len(b) <= 30:
                base.add(a + b)
                base.add(a + b + '123')
    return sorted(base)


def generate_wordlist(inputs: List[str], out_path: str = "custom_wordlist.txt") -> None:
    """
    Generate a bounded custom wordlist from inputs and write to out_path.
    This function tries to be safe about explosion of combinations.
    """
    print("--- Generating Wordlist ---")
    base_words = build_base_words(inputs)
    print(f"Base words count (after basic transforms): {len(base_words)}")

    all_words = set(base_words)

    # For each base word, generate leet variants (bounded)
    for w in base_words:
        # skip extremely long words
        if len(w) > 40:
            continue
        leet_vars = generate_leet_variants(w, cap=500)
        all_words.update(leet_vars)

        # also add simple numeric suffix/prefix combos
        for year in range(1990, 2026, 5):  # a small representative set of years
            if len(all_words) >= MAX_FINAL_WORDLIST_SIZE:
                break
            all_words.add(f"{w}{year}")
            all_words.add(f"{year}{w}")
        # common numeric endings
        if len(all_words) < MAX_FINAL_WORDLIST_SIZE:
            all_words.add(w + "007")
            all_words.add(w + "1234")

        if len(all_words) >= MAX_FINAL_WORDLIST_SIZE:
            print("Reached safety cap for final wordlist size.")
            break

    # Final cleanup: sort, cap
    final_list = sorted(all_words)
    if len(final_list) > MAX_FINAL_WORDLIST_SIZE:
        final_list = final_list[:MAX_FINAL_WORDLIST_SIZE]

    # Write to file
    with open(out_path, "w", encoding="utf-8") as f:
        for item in final_list:
            f.write(item + "\n")

    print(f"✅ Wordlist generated: {out_path}")
    print(f"Total entries written: {len(final_list)}")
    # print first 20 lines as a sample
    print("\nSample (first 20 entries):")
    for i, it in enumerate(final_list[:20], start=1):
        print(f"{i:02d}. {it}")
    print("----------------------------------\n")


def interactive_mode():
    """Prompt user for inputs if CLI not provided."""
    print("Interactive mode — please provide inputs.")
    pwd = input("Enter a password to analyze (won't be stored): ").strip()
    raw_inputs = input("Enter words for wordlist (e.g. name pet year), separated by spaces: ").strip()
    if not raw_inputs:
        print("No inputs provided; using a small default set ['password','admin','user']")
        inputs = ["password", "admin", "user"]
    else:
        inputs = raw_inputs.split()
    return pwd, inputs


def parse_cli():
    parser = argparse.ArgumentParser(description="Password Strength Analyzer & Custom Wordlist Generator")
    parser.add_argument("--password", help="Password to analyze")
    parser.add_argument("--inputs", nargs="+", help="User inputs for wordlist (name, pet, date, etc.)")
    parser.add_argument("--out", help="Output filename for generated wordlist", default="custom_wordlist.txt")
    return parser.parse_args()


def main():
    args = parse_cli()

    if not args.password and not args.inputs:
        # fallback to interactive prompt
        password, inputs = interactive_mode()
    elif args.password and args.inputs:
        password = args.password
        inputs = args.inputs
    else:
        # Partial usage: if password provided but not inputs (or vice versa) prompt for missing piece
        if not args.password:
            password = input("Enter a password to analyze: ").strip()
        else:
            password = args.password
        if not args.inputs:
            raw = input("Enter words for wordlist (name pet year): ").strip()
            inputs = raw.split() if raw else []
        else:
            inputs = args.inputs

    if not password:
        print("No password given — exiting.")
        sys.exit(1)

    # Analyze
    try:
        analyze_password(password)
    except Exception as e:
        print("Error analyzing password:", e)

    # Generate wordlist (if inputs empty, warn and confirm)
    if not inputs:
        print("No custom inputs provided; will still generate a small list from password-derived variants.")
        # Use parts of the password as seeds
        seeds = set()
        seeds.add(password)
        if len(password) >= 4:
            seeds.add(password[:4])
        inputs = list(seeds)

    try:
        generate_wordlist(inputs, out_path=args.out if hasattr(args, "out") else "custom_wordlist.txt")
    except Exception as e:
        print("Error generating wordlist:", e)


if __name__ == "__main__":
    main()
