using System.Net;
using Microsoft.AspNetCore.Mvc.Testing;

namespace LeetLingo.Api.Tests;

public class HealthTests(WebApplicationFactory<Program> api)
    : IClassFixture<WebApplicationFactory<Program>>
{
    private const string TheApiSaysItIsUp = """{"status":"ok"}""";

    [Fact]
    public async Task The_api_answers_that_it_is_up_with_neither_postgres_nor_the_executor_running()
    {
        var answered = await api.CreateClient().GetAsync("/health");

        Assert.Equal(HttpStatusCode.OK, answered.StatusCode);
        Assert.Equal(TheApiSaysItIsUp, await answered.Content.ReadAsStringAsync());
    }
}
