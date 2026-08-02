using System.Text.Json;

namespace LeetLingo.Api.Problems;

public sealed record TestCase(IReadOnlyList<JsonElement> Input, JsonElement ExpectedOutput)
{
    public bool Equals(TestCase? other) =>
        other is not null
        && JsonElement.DeepEquals(ExpectedOutput, other.ExpectedOutput)
        && Input.Count == other.Input.Count
        && Input.Zip(other.Input).All(both => JsonElement.DeepEquals(both.First, both.Second));

    public override int GetHashCode() => HashCode.Combine(Input.Count, ExpectedOutput.ValueKind);
}

public static class TestCases
{
    private static readonly JsonSerializerOptions WrittenDown =
        new() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };

    public static IReadOnlyList<TestCase> From(string document) =>
        JsonSerializer.Deserialize<IReadOnlyList<TestCase>>(document, WrittenDown)!;

    public static string AsOneDocument(IReadOnlyList<TestCase> testCases) =>
        JsonSerializer.Serialize(testCases, WrittenDown);
}
