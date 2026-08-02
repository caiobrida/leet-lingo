using LeetLingo.Api;
using LeetLingo.Api.Problems;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<LeetLingoContext>(options =>
    options.UseNpgsql(
        builder.Configuration.GetConnectionString(LeetLingoContext.TheConnectionStringItReads)));

var app = builder.Build();

app.MapGet("/health", () => new Health("ok"));

app.MapGet("/problems/{slug}", async (
    string slug,
    LeetLingoContext catalogue,
    CancellationToken givenUpOn) =>
    await catalogue.ReadTheProblem(slug, givenUpOn) is { } problem
        ? Results.Ok(problem)
        : Results.NotFound());

app.Run();
