"""
min_context.py

A library to calculate the minimum number of consecutive lines needed for all sets of lines to be unique in a file.
"""

def calculate_min_context(file_content: list[str]) -> int:
    """
    Calculate the minimum k such that all consecutive k-line windows in the file_content are unique.

    :param file_content: List of strings representing the lines of the file.
    :return: The minimum k where no duplicate consecutive k-lines exist.
    :raises ValueError: If the file is empty or uniqueness cannot be achieved (though unlikely).
    """
    n = len(file_content)
    if n == 0:
        raise ValueError("File content is empty.")

    k = 1
    while k <= n:
        windows = set()
        duplicate_found = False
        for i in range(n - k + 1):
            window = tuple(file_content[i:i + k])
            if window in windows:
                duplicate_found = True
                break
            windows.add(window)
        if not duplicate_found:
            return k
        k += 1

    # If no unique k found (entire file is repeated, but impossible for k=n unless n=0)
    raise ValueError("Unable to find a unique context size.")

# Example usage (for testing)
if __name__ == "__main__":
    # Test case 1: Duplicates at small k
    test_content = ["a", "b", "a", "b", "c"]
    print(calculate_min_context(test_content))  # Expected: 3

    # Test case 2: All unique lines
    test_content2 = ["line1", "line2", "line3"]
    print(calculate_min_context(test_content2))  # Expected: 1

    # Test case 3: With blanks
    test_content3 = ["", "a", "", "a", ""]
    print(calculate_min_context(test_content3))  # Expected: 3 (since ("", "a", "") duplicates if k=3 unique? Wait, positions 0-2: "",a,"" ; 1-3: a,"",a ; 2-4: "","a","" so duplicate at k=3? No, 0-2 and 2-4 are both "",a,"" so duplicate, k=4: 0-3: "",a,"",a ; 1-4: a,"",a,"" unique? Yes if no duplicate.
    # Actually for this, k=4: two windows: 0-3: ("","a","","a"), 1-4: ("a","","a","") different, so unique.
    # k=3: 0-2: ("","a",""), 1-3: ("a","","a"), 2-4: ("","a","") duplicate with 0-2.
    # So return 4