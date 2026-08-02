using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using LeetLingo.Api.Problems;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace LeetLingo.Api.Tests;

public class ProblemTests(TheApiWithItsCatalogue api) : IClassFixture<TheApiWithItsCatalogue>
{
    private const string ASeededProblem = "two-sum";

    private const string ASlugNoProblemCarries = "a-problem-nobody-has-written";

    private const string TheSignatureOfTwoSum =
        "def solve(numbers: list[int], target: int) -> list[int]";

    private const string BothHalvesOfEveryTestCaseOfTwoSum =
        """[{"input":[[2,7,11,15],9],"expectedOutput":[0,1]},"""
        + """{"input":[[3,2,4],6],"expectedOutput":[1,2]},"""
        + """{"input":[[3,3],6],"expectedOutput":[0,1]}]""";

    [Fact]
    public async Task A_problem_is_read_by_the_slug_that_names_it()
    {
        var answered = await api.CreateClient().GetAsync($"/problems/{ASeededProblem}");

        Assert.Equal(HttpStatusCode.OK, answered.StatusCode);

        var problem = await answered.Content.ReadFromJsonAsync<JsonElement>();

        Assert.Equal(ASeededProblem, problem.GetProperty("slug").GetString());
        Assert.Equal("Two Sum", problem.GetProperty("title").GetString());
        Assert.Equal(TheSignatureOfTwoSum, problem.GetProperty("functionSignature").GetString());
        Assert.StartsWith("Given a list of integers", problem.GetProperty("statement").GetString());
    }

    [Fact]
    public async Task Both_halves_of_every_test_case_a_problem_is_judged_against_are_read_with_it()
    {
        var answered = await api.CreateClient().GetAsync($"/problems/{ASeededProblem}");

        var problem = await answered.Content.ReadFromJsonAsync<JsonElement>();

        Assert.Equal(BothHalvesOfEveryTestCaseOfTwoSum, problem.GetProperty("testCases").GetRawText());
    }

    [Fact]
    public async Task A_slug_no_problem_carries_is_not_found_and_says_nothing_about_the_catalogue()
    {
        var answered = await api.CreateClient().GetAsync($"/problems/{ASlugNoProblemCarries}");

        Assert.Equal(HttpStatusCode.NotFound, answered.StatusCode);
        Assert.Empty(await answered.Content.ReadAsStringAsync());
    }

    [Fact]
    public async Task The_catalogue_comes_from_the_migration_and_is_the_same_on_every_fresh_database()
    {
        using var scope = api.Services.CreateScope();
        var catalogue = scope.ServiceProvider.GetRequiredService<LeetLingoContext>();

        Assert.NotEmpty(await catalogue.Database.GetAppliedMigrationsAsync());
        Assert.Equal(
            TheSeededCatalogue.TwoSum,
            (await catalogue.Problems.SingleAsync(problem => problem.Slug == ASeededProblem)).Id);
    }
}
