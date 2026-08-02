using System.Text.Json;

namespace LeetLingo.Api.Problems;

public record TestCase(IReadOnlyList<JsonElement> Input, JsonElement ExpectedOutput);

public static class TestCases
{
    private static readonly JsonSerializerOptions WrittenDown = new(JsonSerializerDefaults.Web);

    public static IReadOnlyList<TestCase> From(string document) =>
        JsonSerializer.Deserialize<IReadOnlyList<TestCase>>(document, WrittenDown)!;

    public static string AsOneDocument(IReadOnlyList<TestCase> testCases) =>
        JsonSerializer.Serialize(testCases, WrittenDown);
}
