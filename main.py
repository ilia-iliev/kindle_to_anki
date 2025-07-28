import argparse
from kindle_detector import (
    KindleDetector,
    KindleNotAttachedError,
    KindleNotReadableError,
)
from kindle_reader import KindleReader
from anki_importer import CSVExporter, CSVExportError


def main():
    """Main function implementing features 1.1, 1.2, and 2.1 from PRD."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Kindle to Anki - Reading probable unknown words"
    )
    parser.add_argument(
        "--test", action="store_true", help="Fetch random 10 words for testing"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to save the CSV file (default: current directory)",
    )
    args = parser.parse_args()

    print("Kindle to Anki - Reading probable unknown words")
    print("=" * 50)

    # Initialize Kindle detector
    detector = KindleDetector()

    try:
        # Feature 1.1: Detect if Kindle is attached and readable
        print("Checking if Kindle device is attached...")
        detector.detect_kindle()
        print("✓ Kindle device detected and accessible!")
        print(f"Kindle found at: {detector.mount_path}")

        # Feature 1.2: Read words from Kindle database
        print("\nReading words from Kindle database...")
        reader = KindleReader(detector.mount_path)

        if args.test:
            # Test mode: get random 10 words
            print("Running in test mode - fetching random 10 words...")
            print("Loading frequent words for filtering...")
            print("Loading Anki words for filtering...")
            words = reader.get_random_test_words(10)
            print(
                f"✓ Retrieved {len(words)} random test words (frequent words and Anki words filtered out):"
            )
        else:
            # Normal mode: get words since last access
            print("Loading frequent words for filtering...")
            print("Loading Anki words for filtering...")
            words = reader.get_words_since_last_access()
            print(
                f"✓ Retrieved {len(words)} words since last access (frequent words and Anki words filtered out):"
            )

        # Print the words (as requested, not testing for printing)
        for i, word in enumerate(words, 1):
            print(f"  {i}. {word}")

        if not words:
            print("  No new words found.")

        # Feature 3.2: Export words to CSV format with definitions
        if words:
            print("\nFetching word definitions from dictionary...")
            print("Exporting words to CSV with definitions...")
            try:
                exporter = CSVExporter(output_dir=args.output_dir, use_dictionary=True)
                csv_path = exporter.export_words_to_csv(words)
                print(
                    f"✓ Successfully exported {len(words)} words with definitions to: {csv_path}"
                )
            except CSVExportError as e:
                print(f"✗ Failed to export words to CSV: {e}")
        else:
            print("\nNo words to export to CSV.")

        # Show information about frequent words filtering
        print(
            f"\nFrequent words loaded: {len(reader.frequent_words_manager._frequent_words)} words"
        )
        print(
            "Common words like 'the', 'be', 'to', 'of', 'and', etc. have been filtered out."
        )
        print("Words that already exist in Anki have also been filtered out.")

    except KindleNotAttachedError as e:
        print("✗ Kindle device not found!")
        print()
        print(detector.get_helpful_message(e))

        # Debug information
        print("\nDebug information:")
        found_paths = detector.find_kindle_mount_paths()
        if found_paths:
            print(f"Found potential Kindle paths: {found_paths}")
        else:
            print("No potential Kindle paths found")

    except KindleNotReadableError as e:
        print("✗ Kindle device not accessible!")
        print()
        print(detector.get_helpful_message(e))

    except Exception as e:
        print(f"✗ An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
