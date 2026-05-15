import argparse
from kindle.detector import KindleDetector
from kindle.reader import KindleReader
from csv_exporter import CSVExporter
from errors import KindleNotAttachedError, KindleNotReadableError, CSVExportError


def main():
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

    detector = KindleDetector()

    try:
        detector.detect_kindle()
        print(f"Kindle found at: {detector.mount_path}")

        reader = KindleReader(detector.mount_path)

        if args.test:
            words = reader.get_random_test_words(10)
            print(f"Retrieved {len(words)} random test words (filtered):")
        else:
            words = reader.get_words_since_last_access()
            print(f"Retrieved {len(words)} new words since last access (filtered):")

        for i, word in enumerate(words, 1):
            print(f"  {i}. {word}")

        if not words:
            print("  No new words found.")
            return

        print("\nFetching definitions and exporting to CSV...")
        try:
            exporter = CSVExporter(output_dir=args.output_dir)
            csv_path = exporter.export_words_to_csv(words)
            print(f"Exported to: {csv_path}")
        except CSVExportError as e:
            print(f"Failed to export: {e}")

    except KindleNotAttachedError as e:
        print("Kindle device not found!")
        print(detector.get_helpful_message(e))
        found_paths = detector.find_kindle_mount_paths()
        if found_paths:
            print(f"\nFound potential Kindle paths: {found_paths}")

    except KindleNotReadableError as e:
        print("Kindle device not accessible!")
        print(detector.get_helpful_message(e))

    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
