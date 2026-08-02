namespace LeetLingo.Api.Problems;

public static class TheSeededCatalogue
{
    public static readonly Guid TwoSum = new("8f14e45f-ceea-467a-9ba2-0f1b1a1c7d21");

    public static IReadOnlyList<Problem> Problems =>
    [
        new Problem
        {
            Id = TwoSum,
            Slug = "two-sum",
            Title = "Two Sum",
            Statement =
                "Given a list of integers and a target, return the indices of the two numbers "
                + "that add up to the target.\n\n"
                + "Exactly one pair adds up to the target, and the same element may not be used "
                + "twice. Return the two indices in ascending order.",
            FunctionSignature = "def solve(numbers: list[int], target: int) -> list[int]",
            TestCases = TestCases.From(
                """
                [
                  { "input": [[2, 7, 11, 15], 9], "expectedOutput": [0, 1] },
                  { "input": [[3, 2, 4], 6], "expectedOutput": [1, 2] },
                  { "input": [[3, 3], 6], "expectedOutput": [0, 1] }
                ]
                """),
        },
    ];
}
