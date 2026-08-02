using LeetLingo.Api;
using LeetLingo.Api.Problems;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<LeetLingoContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString(LeetLingoContext.TheDatabaseItReaches)));

var app = builder.Build();

app.MapGet("/health", () => new Health("ok"));

app.MapGet("/problems/{slug}", async (string slug, LeetLingoContext catalogue) =>
    await catalogue.ReadTheProblem(slug) is { } problem
        ? Results.Ok(problem)
        : Results.NotFound());

app.Run();
