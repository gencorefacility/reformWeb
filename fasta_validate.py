import re
import sys

def contains_only_letters(seq, verbose=False):
    """
    1. Sequence lines can't be empty.
    2. Sequence lines must only contain the characters [A-Z] and [a-z].
    """
    if not seq:
        if verbose:
            print("ERROR: Sequence line is empty. Sequence lines cannot be empty.")
        return False
    if not re.match(r"^[A-Za-z]+$", seq):
        if verbose:
            print("ERROR: Sequence contains invalid characters. Only letters [A-Za-z] are allowed.")
        return False
    return True

def check_identifier_format(line, verbose=False):
    """
    1. Each header line starts with a '>' and followed by a non-space identifier.
    """
    if not re.match(r"^>\S+", line):
        if verbose:
            print("ERROR: Invalid identifier format. Header lines must start with '>' followed by a non-space identifier.")
        return False
    return True

def validate_fasta(filename, verbose=False):
    try:
        with open(filename, "r") as fp:
            unique_ids = set()
            firstline = True
            seqcount = 0
            in_sequence = False

            for line_num, line in enumerate(fp, 1):
                line = line.strip()

                # Check empty line
                if not line:
                    if verbose:
                        print(f"ERROR: Empty line detected at line {line_num}. Empty lines are not allowed.")
                    return False

                # Check header line
                if line.startswith(">"):
                    if not firstline and seqcount == 0:
                        if verbose:
                            print(f"ERROR: Empty sequence found after header at line {line_num - 1}.")
                        return False

                    firstline = False
                    seqcount = 0
                    in_sequence = True

                    # Check format of header line
                    if not check_identifier_format(line, verbose):
                        return False

                    # Check duplicate header
                    line_id = line[1:].split(" ")[0]
                    if line_id in unique_ids:
                        if verbose:
                            print(f"ERROR: Duplicate ID found: {line_id}. Each sequence identifier must be unique.")
                        return False
                    unique_ids.add(line_id)
                else:
                    # Check duplicate header lien
                    if firstline:
                        if verbose:
                            print(f"ERROR: The first line should start with '>'. Found at line {line_num}.")
                        return False

                    # Check sequence lines
                    if not contains_only_letters(line, verbose):
                        return False

                    # recourd lenght
                    seqcount += len(line)

            # Check final sequence
            if seqcount == 0:
                if verbose:
                    print("ERROR: Final sequence is empty.")
                return False

        # Passed
        if verbose:
            print("FASTA file format is valid.")
        return True

    except FileNotFoundError:
        if verbose:
            print(f"ERROR: Can't open file {filename}.")
        return False
    except MemoryError:
        if verbose:
            print("ERROR: Memory allocation issue.")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python fasta_validate.py [fasta file]")
        sys.exit(1)

    verbose = True
    filename = sys.argv[1]

    result = validate_fasta(filename, verbose)
    if not result:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()