namespace LeetLingo.Api.Problems;

public class Problem
{
    public required Guid Id { get; init; }
    public required string Slug { get; init; }
    public required string Title { get; init; }
    public required string Statement { get; init; }
    public required string FunctionSignature { get; init; }
    public required IReadOnlyList<TestCase> TestCases { get; init; }
}
