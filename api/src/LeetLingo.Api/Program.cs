using LeetLingo.Api;

var builder = WebApplication.CreateBuilder(args);

var app = builder.Build();

app.MapGet("/health", () => new Health("ok"));

app.Run();
