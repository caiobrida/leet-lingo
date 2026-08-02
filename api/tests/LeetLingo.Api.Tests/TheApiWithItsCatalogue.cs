using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Testcontainers.PostgreSql;

namespace LeetLingo.Api.Tests;

public class TheApiWithItsCatalogue : WebApplicationFactory<Program>, IAsyncLifetime
{
    private const string ThePostgresTheSuiteOwns = "postgres:17-alpine";

    private readonly PostgreSqlContainer postgres =
        new PostgreSqlBuilder(ThePostgresTheSuiteOwns).Build();

    public async Task InitializeAsync()
    {
        await postgres.StartAsync();

        await using var scope = Services.CreateAsyncScope();
        await scope.ServiceProvider.GetRequiredService<LeetLingoContext>().Database.MigrateAsync();
    }

    async Task IAsyncLifetime.DisposeAsync()
    {
        await base.DisposeAsync();
        await postgres.DisposeAsync();
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder) =>
        builder.UseSetting(
            $"ConnectionStrings:{LeetLingoContext.TheConnectionStringItReads}",
            postgres.GetConnectionString());
}
