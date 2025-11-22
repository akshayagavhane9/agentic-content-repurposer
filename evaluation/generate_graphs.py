import os
import pandas as pd
import matplotlib.pyplot as plt


def load_results():
    """Load test_results.csv and handle both with/without header cases."""
    csv_path = os.path.join(os.path.dirname(__file__), "test_results.csv")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Could not find {csv_path}")

    # Peek at first line to see if there is a header
    with open(csv_path, "r") as f:
        first_line = f.readline().strip()

    has_header = first_line.lower().startswith("test_case")

    if has_header:
        df = pd.read_csv(csv_path)
    else:
        df = pd.read_csv(
            csv_path,
            header=None,
            names=["test_case", "linkedin", "instagram", "email", "timestamp"],
        )

    return df


def main():
    df = load_results()

    # Basic sanity print
    print("Loaded results:")
    print(df[["test_case", "linkedin", "instagram", "email"]])

    # Create line chart of scores across test cases
    plt.figure(figsize=(10, 6))

    plt.plot(df["test_case"], df["linkedin"], marker="o", label="LinkedIn")
    plt.plot(df["test_case"], df["instagram"], marker="o", label="Instagram")
    plt.plot(df["test_case"], df["email"], marker="o", label="Email")

    plt.title("Quality Scores Across Test Cases")
    plt.xlabel("Test Case")
    plt.ylabel("Quality Score")
    plt.legend()
    plt.grid(True)

    out_path = os.path.join(os.path.dirname(__file__), "quality_scores.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"\nSaved graph as: {out_path}")


if __name__ == "__main__":
    main()
