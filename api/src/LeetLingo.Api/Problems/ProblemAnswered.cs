namespace LeetLingo.Api.Problems;

public record ProblemAnswered(
    string Slug,
    string Title,
    string Statement,
    string FunctionSignature,
    IReadOnlyList<TestCase> TestCases);
